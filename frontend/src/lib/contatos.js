// Monta a lista de redes sociais de um perfil (Instagram, Discord e X).
// Aceita qualquer objeto com os campos instagram, discord e x.

function semArroba(valor) {
  return String(valor || '').trim().replace(/^@+/, '');
}

export function montarRedes(perfil) {
  if (!perfil) return [];

  const lista = [];

  const instagram = semArroba(perfil.instagram);
  const discord = String(perfil.discord || '').trim();
  const x = semArroba(perfil.x);

  if (instagram) {
    lista.push({
      chave: 'instagram',
      icone: '📷',
      texto: `@${instagram}`,
      href: `https://instagram.com/${encodeURIComponent(instagram)}`
    });
  }

  if (discord) {
    lista.push({
      chave: 'discord',
      icone: '🎮',
      texto: discord,
      href: null
    });
  }

  if (x) {
    lista.push({
      chave: 'x',
      icone: '✕',
      texto: `@${x}`,
      href: `https://x.com/${encodeURIComponent(x)}`
    });
  }

  return lista;
}