import { Component } from "react";

// Se um gráfico quebrar (dado inesperado, erro da biblioteca de gráficos), a
// resposta não pode sumir: mostra o `alternativo` (a tabela) no lugar. O erro
// vai para o console para quem estiver depurando.
export default class LimiteErro extends Component {
  constructor(props) {
    super(props);
    this.state = { erro: null };
  }

  static getDerivedStateFromError(erro) {
    return { erro };
  }

  componentDidCatch(erro, info) {
    console.error("Falha ao desenhar o gráfico; mostrando a tabela.", erro, info?.componentStack);
  }

  componentDidUpdate(anteriores) {
    // Trocou o que está sendo desenhado (outro modo, outra resposta): tenta de novo.
    if (this.state.erro && anteriores.chave !== this.props.chave) this.setState({ erro: null });
  }

  render() {
    if (this.state.erro) return this.props.alternativo ?? null;
    return this.props.children;
  }
}
