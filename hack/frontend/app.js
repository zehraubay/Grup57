function showProductSection() {
  document.getElementById("product-section").style.display = "block";
  document.getElementById("kriz-section").style.display = "none";
}

function showKrizSection() {
  document.getElementById("kriz-section").style.display = "block";
  document.getElementById("product-section").style.display = "none";
}

async function sendBarkod() {
  const barkod = document.getElementById("barkodInput").value;
  const token = localStorage.getItem("token"); // login sonrası kaydedilmiş olmalı

  const res = await fetch("http://localhost:8000/greenlens/scan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({ barcode: barkod }) // 🔁 'barkod' değil 'barcode'
  });

  const data = await res.json();
  document.getElementById("barkodResult").textContent = JSON.stringify(data, null, 2);
}


async function sendKriz() {
  const kriz = document.getElementById("krizSelect").value;
  const yil = document.getElementById("yilSelect").value;
  const res = await fetch("http://localhost:8000/kriz", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kriz, yil })
  });
  const data = await res.json();
  document.getElementById("krizResult").textContent = JSON.stringify(data, null, 2);
}
