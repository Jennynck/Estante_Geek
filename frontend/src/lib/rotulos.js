// Nomenclatura das unidades de uma obra.
// Mangá é dividido em volumes. HQ (série da Comic Vine) é dividida em edições.
// Concentrar isso aqui evita repetir a regra em cada tela.

const ehHQ = (tipo) => tipo === 'HQ';

// "Volumes" ou "Edições" (rótulo de indicador, cabeçalho de lista)
export function etiquetaUnidade(tipo) {
  return ehHQ(tipo) ? 'Edições' : 'Volumes';
}

// "volume(s)" ou "edição/edições", conforme a quantidade
export function unidadeObra(tipo, quantidade = 2) {
  if (quantidade === 1) return ehHQ(tipo) ? 'edição' : 'volume';
  return ehHQ(tipo) ? 'edições' : 'volumes';
}

// O backend grava os títulos como "Volume N" para os dois tipos.
// Para HQ, exibimos "Edição N" sem mexer no banco.
export function tituloUnidade(tipo, linhaVolume) {
  const numero = linhaVolume?.numero_volume;
  const original = linhaVolume?.titulo_volume || '';

  if (!ehHQ(tipo)) return original || `Volume ${numero}`;

  if (!original || /^volume\s+\d+$/i.test(original.trim())) {
    return `Edição ${numero}`;
  }
  return original;
}