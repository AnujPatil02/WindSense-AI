"""
Multimodal RAG using CLIP — image-based fault retrieval.
Indexes turbine damage images alongside text manuals.
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict
from loguru import logger

MODELS_DIR = Path("outputs/models")
IMAGE_DIR  = Path("data/rag_docs/images")
IMAGE_DIR.mkdir(exist_ok=True, parents=True)


def _load_clip():
    """Load CLIP model and preprocessing."""
    try:
        import clip
        import torch
        device = "cuda" if __import__("torch").cuda.is_available() else "cpu"
        model, preprocess = clip.load("ViT-B/32", device=device)
        return model, preprocess, device
    except ImportError:
        logger.warning("CLIP not installed — multimodal RAG unavailable")
        return None, None, None


def index_images(image_dir: Path = IMAGE_DIR) -> Dict:
    """
    Build CLIP embeddings for all images in image_dir.
    Saves embeddings + metadata for retrieval.
    """
    model, preprocess, device = _load_clip()
    if model is None:
        return {"status": "CLIP not available"}

    import torch
    from PIL import Image

    image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
    if not image_files:
        logger.warning(f"No images found in {image_dir}")
        _generate_synthetic_damage_images(image_dir)
        image_files = list(image_dir.glob("*.png"))

    embeddings = []
    metadata   = []

    for img_path in image_files:
        try:
            image   = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
            with torch.no_grad():
                emb = model.encode_image(image).cpu().numpy()[0]
            embeddings.append(emb / (np.linalg.norm(emb) + 1e-8))
            metadata.append({
                "path"     : str(img_path),
                "filename" : img_path.name,
                "label"    : img_path.stem.replace("_", " "),
            })
            logger.info(f"Indexed image: {img_path.name}")
        except Exception as e:
            logger.error(f"Image indexing failed for {img_path.name}: {e}")

    if embeddings:
        index_data = {
            "embeddings": np.array(embeddings, dtype=np.float32),
            "metadata"  : metadata,
        }
        with open(MODELS_DIR / "clip_index.pkl", "wb") as f:
            pickle.dump(index_data, f)
        logger.success(f"CLIP index built: {len(embeddings)} images")
        return {"status": "success", "n_images": len(embeddings)}

    return {"status": "no_images"}


def search_by_text(query: str, top_k: int = 3) -> List[Dict]:
    """Find most similar images given a text query."""
    model, preprocess, device = _load_clip()
    if model is None:
        return []

    import torch
    import clip

    index_path = MODELS_DIR / "clip_index.pkl"
    if not index_path.exists():
        logger.warning("CLIP index not found — run index_images() first")
        return []

    with open(index_path, "rb") as f:
        index_data = pickle.load(f)

    embeddings = index_data["embeddings"]
    metadata   = index_data["metadata"]

    # Encode text query
    tokens = clip.tokenize([query]).to(device)
    with torch.no_grad():
        text_emb = model.encode_text(tokens).cpu().numpy()[0]
    text_emb /= (np.linalg.norm(text_emb) + 1e-8)

    # Cosine similarity
    scores  = embeddings @ text_emb
    top_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_idx:
        results.append({
            **metadata[idx],
            "similarity": round(float(scores[idx]), 4),
        })
    return results


def _generate_synthetic_damage_images(image_dir: Path):
    """Generate simple synthetic damage visualization images for demo."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        damage_types = {
            "bearing_spalling"      : ("red",    "Bearing Spalling Detected"),
            "gear_tooth_pitting"    : ("orange", "Gear Tooth Pitting"),
            "rotor_blade_crack"     : ("purple", "Rotor Blade Surface Crack"),
            "oil_contamination"     : ("brown",  "Oil Contamination - Dark"),
            "normal_bearing_surface": ("green",  "Normal Bearing Surface"),
        }

        for name, (color, label) in damage_types.items():
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.set_facecolor("lightgray")

            # Simulate damage pattern
            if color != "green":
                for _ in range(20):
                    x, y = np.random.uniform(0.1, 0.9, 2)
                    r    = np.random.uniform(0.01, 0.05)
                    circle = plt.Circle((x, y), r, color=color, alpha=0.6)
                    ax.add_patch(circle)
            else:
                circle = plt.Circle((0.5, 0.5), 0.3, color="green",
                                     alpha=0.3, fill=True)
                ax.add_patch(circle)

            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_title(label, fontsize=10)
            ax.axis("off")
            fig.savefig(image_dir / f"{name}.png", dpi=100, bbox_inches="tight")
            plt.close()

        logger.info(f"Generated {len(damage_types)} synthetic damage images")
    except Exception as e:
        logger.error(f"Synthetic image generation failed: {e}")


if __name__ == "__main__":
    result = index_images()
    print(f"Index result: {result}")

    results = search_by_text("bearing damage spalling", top_k=3)
    print("\nImage search results for 'bearing damage spalling':")
    for r in results:
        print(f"  [{r['similarity']:.4f}] {r['filename']} — {r['label']}")