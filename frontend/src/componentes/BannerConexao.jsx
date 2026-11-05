import { useEffect, useState } from "react";
import Icone from "./Icone";

// Aviso de conexão: aparece quando o navegador perde a internet e, por alguns
// segundos, quando ela volta. Sem isso, perguntas falhavam com "não consegui
// falar com o servidor" sem a pessoa saber que o problema era a rede dela.
export default function BannerConexao() {
  const [online, setOnline] = useState(() => (typeof navigator === "undefined" ? true : navigator.onLine));
  const [voltou, setVoltou] = useState(false);

  useEffect(() => {
    let timer;
    function aoCair() {
      clearTimeout(timer);
      setVoltou(false);
      setOnline(false);
    }
    function aoVoltar() {
      setOnline(true);
      setVoltou(true);
      timer = setTimeout(() => setVoltou(false), 3500);
    }
    window.addEventListener("offline", aoCair);
    window.addEventListener("online", aoVoltar);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("offline", aoCair);
      window.removeEventListener("online", aoVoltar);
    };
  }, []);

  if (online && !voltou) return <div className="sr-only" role="status" aria-live="polite" />;
  return (
    <div className={`banner-conexao ${online ? "ok" : "fora"}`} role="status" aria-live="polite">
      <Icone nome={online ? "check" : "alerta"} size={16} />
      {online
        ? "Conexão restabelecida."
        : "Você está sem internet. As perguntas e o panorama voltam a funcionar assim que a conexão voltar."}
    </div>
  );
}
