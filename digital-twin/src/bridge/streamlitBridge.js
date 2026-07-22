// Sends turbine click events to the parent Streamlit page via postMessage.
export function notifyParent(eventType, payload) {
  try {
    window.parent.postMessage({ source: "windsense-digital-twin", eventType, payload }, "*");
  } catch (e) {
    // running standalone (npm run dev) outside an iframe - safe to ignore
  }
}
