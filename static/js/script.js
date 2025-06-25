document.addEventListener("DOMContentLoaded", function () {
  M.AutoInit();

  M.FormSelect.init(document.querySelectorAll("select"));

  M.Datepicker.init(document.querySelectorAll(".datepicker"), {
    format: "dd/mm/yyyy",
    autoClose: true,
  });

  document.querySelectorAll(".datetime").forEach((el) => {
    el.type = "datetime-local";
  });

  document.querySelectorAll(".toggle-delete-icon").forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const label = this.closest("label");
      const checkbox = label?.querySelector('input[type="checkbox"]');
      const icon = this.querySelector("i");

      if (checkbox && icon) {
        checkbox.checked = !checkbox.checked;
        icon.textContent = checkbox.checked ? "delete" : "delete_outline";
      }
    });
  });

  const cepInput = document.getElementById("cep");
  const numberInput = document.getElementById("number");

  if (cepInput) {
    cepInput.addEventListener("blur", function () {
      const cep = cepInput.value.replace(/\D/g, "");
      const number = numberInput?.value || "";

      if (cep.length === 8) {
        fetch(`https://viacep.com.br/ws/${cep}/json/`)
          .then((res) => res.json())
          .then((data) => {
            if (!data.erro) {
              const rua = data.logradouro || "";
              const bairro = data.bairro || "";
              const cidade = data.localidade || "";
              const uf = data.uf || "";
              const cepFormatado = data.cep || cep;

              const enderecoCompleto = `${rua}, ${number} - ${bairro}, ${cidade}/${uf} - CEP: ${cepFormatado}`;
              const addressField = document.getElementById("address");
              if (addressField) {
                addressField.value = enderecoCompleto;
              }
            }
          });
      }
    });
  }

  if (numberInput) {
    numberInput.addEventListener("blur", () => {
      if (cepInput && cepInput.value.trim()) {
        cepInput.dispatchEvent(new Event("blur"));
      }
    });
  }

  document.querySelectorAll("#add-detail").forEach((btn) => {
    btn.addEventListener("click", addDetailRow);
  });

  const imageInput = document.getElementById("image-upload");
  if (imageInput) {
    imageInput.addEventListener("change", handleImagePreview);
  }
});

function addDetailRow() {
  const tbody = document.querySelector("#details-table tbody");
  if (!tbody) return;

  const row = document.createElement("tr");
  row.innerHTML = `
    <td><input type="text" class="key-field" /></td>
    <td><input type="text" class="value-field" /></td>
    <td class="right">
      <a class="btn-small red" onclick="this.closest('tr').remove()" title="Remove">
        <i class="material-icons">delete</i>
      </a>
    </td>
  `;
  tbody.appendChild(row);
  M.updateTextFields();
}

function serializeDetailsToJson() {
  const rows = document.querySelectorAll("#details-table tbody tr");
  const details = {};
  rows.forEach((row) => {
    const key = row.querySelector(".key-field")?.value.trim();
    const value = row.querySelector(".value-field")?.value.trim();
    if (key) details[key] = value;
  });

  const target = document.getElementById("details-json");
  if (target) {
    target.value = JSON.stringify(details);
  }
}

let newFiles = [];

function handleImagePreview(e) {
  const files = Array.from(e.target.files);
  const previewWrapper = document.getElementById("preview-wrapper");
  const addImageCard = document.getElementById("add-image-card");
  if (!previewWrapper || !addImageCard) return;

  files.forEach((file) => {
    const reader = new FileReader();
    reader.onload = function (ev) {
      const col = document.createElement("div");
      col.className = "col s12 m6 l3 preview-container";

      const card = document.createElement("div");
      card.className = "card";

      const cardImage = document.createElement("div");
      cardImage.className = "card-image";

      const img = document.createElement("img");
      img.src = ev.target.result;
      img.className = "thumbnail";

      const deleteBtn = document.createElement("a");
      deleteBtn.className = "btn-floating red fab-top-right";
      deleteBtn.innerHTML = '<i class="material-icons">close</i>';
      deleteBtn.onclick = () => {
        previewWrapper.removeChild(col);
        newFiles = newFiles.filter((f) => f !== file);
        updateFileInput();
      };

      cardImage.appendChild(img);
      cardImage.appendChild(deleteBtn);
      card.appendChild(cardImage);
      col.appendChild(card);
      previewWrapper.insertBefore(col, addImageCard);
    };
    reader.readAsDataURL(file);
    newFiles.push(file);
  });

  updateFileInput();
}

function updateFileInput() {
  const imageInput = document.getElementById("image-upload");
  if (!imageInput) return;

  const dataTransfer = new DataTransfer();
  newFiles.forEach((f) => dataTransfer.items.add(f));
  imageInput.files = dataTransfer.files;
}
