// A foto de perfil é guardada como data URL no localStorage (mesma "camada de
// mentira" do auth.js). O localStorage tem cota de ~5MB por origem, e uma foto
// de celular sozinha passa disso — então redimensionamos antes de guardar.
//
// Com backend real isto vira um upload multipart e o que fica guardado é a URL
// devolvida pelo servidor, não a imagem inteira.

export const TAMANHO_MAX_MB = 5;
const LADO_MAX = 320; // suficiente para o avatar em telas retina
const QUALIDADE = 0.85;

const TIPOS_ACEITOS = ["image/jpeg", "image/png", "image/webp"];

/** "" quando o arquivo serve; senão a mensagem para o usuário. */
export function validarImagem(arquivo) {
  if (!arquivo) return "Escolha uma imagem.";
  if (!TIPOS_ACEITOS.includes(arquivo.type))
    return "Use uma imagem JPG, PNG ou WebP.";
  if (arquivo.size > TAMANHO_MAX_MB * 1024 * 1024)
    return `A imagem precisa ter no máximo ${TAMANHO_MAX_MB} MB.`;
  if (arquivo.size === 0) return "Esse arquivo está vazio.";
  return "";
}

function lerComoDataUrl(arquivo) {
  return new Promise((resolve, reject) => {
    const leitor = new FileReader();
    leitor.onload = () => resolve(leitor.result);
    leitor.onerror = () => reject(new Error("falha ao ler o arquivo"));
    leitor.readAsDataURL(arquivo);
  });
}

/**
 * Recorta no centro (quadrado) e reduz para LADO_MAX. Devolve um data URL
 * JPEG pequeno o bastante para caber no localStorage.
 */
export async function prepararFoto(arquivo) {
  const dataUrl = await lerComoDataUrl(arquivo);

  const img = await new Promise((resolve, reject) => {
    const el = new Image();
    el.onload = () => resolve(el);
    el.onerror = () => reject(new Error("imagem inválida"));
    el.src = dataUrl;
  });

  const lado = Math.min(img.width, img.height);
  const origemX = (img.width - lado) / 2;
  const origemY = (img.height - lado) / 2;
  const destino = Math.min(lado, LADO_MAX);

  const canvas = document.createElement("canvas");
  canvas.width = destino;
  canvas.height = destino;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, origemX, origemY, lado, lado, 0, 0, destino, destino);

  return canvas.toDataURL("image/jpeg", QUALIDADE);
}
