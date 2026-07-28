import { ImageResponse } from "next/og";

export const alt = "IdentityCore identity infrastructure and orchestration";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div
      style={{
        alignItems: "center",
        background:
          "radial-gradient(circle at top left, #2563eb 0, #0f172a 48%, #020617 100%)",
        color: "white",
        display: "flex",
        height: "100%",
        justifyContent: "center",
        padding: "72px",
        width: "100%",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", maxWidth: 980 }}>
        <div style={{ color: "#93c5fd", display: "flex", fontSize: 28 }}>
          IdentityCore
        </div>
        <div
          style={{
            display: "flex",
            fontSize: 68,
            fontWeight: 700,
            letterSpacing: "-2px",
            lineHeight: 1.08,
            marginTop: 28,
          }}
        >
          Build your identity stack on one infrastructure layer.
        </div>
        <div
          style={{
            color: "#cbd5e1",
            display: "flex",
            fontSize: 28,
            lineHeight: 1.4,
            marginTop: 32,
          }}
        >
          Workflows · Policies · Evidence · Managed and bring-your-own providers
        </div>
      </div>
    </div>,
    size,
  );
}
