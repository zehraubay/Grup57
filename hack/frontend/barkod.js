window.addEventListener("DOMContentLoaded", async () => {
    const codeReader = new ZXing.BrowserBarcodeReader();
    const videoElement = document.getElementById('video');
    const resultElement = document.getElementById('scan-result');

    try {
      const devices = await codeReader.getVideoInputDevices();
      if (devices.length === 0) throw new Error("Kamera bulunamadı");

      const selectedDeviceId = devices[0].deviceId;

      codeReader.decodeFromVideoDevice(selectedDeviceId, videoElement, async (result, err) => {
        if (result) {
          console.log("📸 Barkod bulundu:", result.getText()); // ✅ DEBUG LOG

          const barcode = result.getText();
          resultElement.textContent = `Barkod: ${barcode}`;

          const token = localStorage.getItem("token");
          console.log("🪪 Token:", token);

          const response = await fetch("http://127.0.0.1:8000/greenlens/scan", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ barcode })
          });

          const data = await response.json();
          resultElement.textContent += `\n\nGemini Raporu:\n${data.report}`;
          codeReader.reset();
        } else if (err && !(err instanceof ZXing.NotFoundException)) {
          console.error("❌ Barkod okuma hatası:", err); // ✅ DEBUG LOG
        } else {
          console.log("⏳ Barkod henüz bulunamadı..."); // ✅ DEBUG LOG
        }
      });
    } catch (err) {
      resultElement.textContent = `Hata: ${err.message}`;
      console.error("🚨 Kamera veya ZXing hatası:", err); // ✅ DEBUG LOG
    }
  });
