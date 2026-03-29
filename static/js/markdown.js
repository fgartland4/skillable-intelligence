const Markdown = (() => {
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  function parseInline(text) {
    return esc(text)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
      .replace(/(\*\*|__)(.+?)\1/g, '<strong>$2</strong>')
      .replace(/(\*|_)(.+?)\1/g, '<em>$2</em>');
  }

  function parseTable(lines) {
    const rows = lines.map(l => l.replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim()));
    if (rows.length < 2 || !/^[-:\s|]+$/.test(lines[1].replace(/\|/g, ''))) return null;
    const headers = rows[0];
    const body = rows.slice(2);
    let html = '<table><thead><tr>' + headers.map(h => `<th>${parseInline(h)}</th>`).join('') + '</tr></thead><tbody>';
    for (const row of body) {
      html += '<tr>' + row.map(c => `<td>${parseInline(c)}</td>`).join('') + '</tr>';
    }
    return html + '</tbody></table>';
  }

  function parseList(lines, start) {
    let i = start;
    let html = '';
    const baseIndent = lines[i].search(/\S/);
    const firstLine = lines[i].trimStart();
    const ordered = /^\d+\.\s/.test(firstLine);
    const tag = ordered ? 'ol' : 'ul';
    html += `<${tag}>`;

    while (i < lines.length) {
      const line = lines[i];
      if (line.trim() === '') { i++; continue; }
      const indent = line.search(/\S/);
      if (indent < baseIndent) break;
      const trimmed = line.trimStart();
      const isItem = /^(\d+\.\s|[-*]\s)/.test(trimmed);
      if (indent === baseIndent && !isItem) break;

      if (indent > baseIndent) {
        const sub = parseList(lines, i);
        html = html.replace(/<\/li>$/, '') + sub.html + '</li>';
        i = sub.end;
        continue;
      }

      const content = trimmed.replace(/^(\d+\.\s|[-*]\s)/, '');
      html += `<li>${parseInline(content)}</li>`;
      i++;
    }
    html += `</${tag}>`;
    return { html, end: i };
  }

  function render(md) {
    if (!md) return '';
    const lines = md.replace(/\r\n/g, '\n').split('\n');
    const blocks = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];

      if (line.trim() === '') { i++; continue; }

      // Code block
      if (line.trimStart().startsWith('```')) {
        const lang = line.trim().slice(3).trim();
        const codeLines = [];
        i++;
        while (i < lines.length && !lines[i].trimStart().startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        i++; // skip closing ```
        const code = esc(codeLines.join('\n'));
        const id = 'cb-' + Math.random().toString(36).slice(2, 8);
        blocks.push(
          `<div class="code-block"><pre><code${lang ? ` class="language-${esc(lang)}"` : ''} id="${id}">${code}</code></pre>` +
          `<button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('${id}').textContent).then(()=>{this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)})">Copy</button></div>`
        );
        continue;
      }

      // Table
      if (line.includes('|') && i + 1 < lines.length && /^[\s|:-]+$/.test(lines[i + 1].replace(/[^|\-:\s]/g, ''))) {
        const tableLines = [];
        while (i < lines.length && lines[i].includes('|') && lines[i].trim() !== '') {
          tableLines.push(lines[i]);
          i++;
        }
        const table = parseTable(tableLines);
        if (table) { blocks.push(table); continue; }
      }

      // Heading
      const headingMatch = line.match(/^(#{1,6})\s+(.*)/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        blocks.push(`<h${level}>${parseInline(headingMatch[2])}</h${level}>`);
        i++;
        continue;
      }

      // Horizontal rule
      if (/^(\*{3,}|-{3,})$/.test(line.trim())) {
        blocks.push('<hr>');
        i++;
        continue;
      }

      // Blockquote
      if (line.trimStart().startsWith('> ')) {
        const quoteLines = [];
        while (i < lines.length && lines[i].trimStart().startsWith('> ')) {
          quoteLines.push(lines[i].trimStart().slice(2));
          i++;
        }
        blocks.push(`<blockquote>${render(quoteLines.join('\n'))}</blockquote>`);
        continue;
      }

      // List
      if (/^\s*(\d+\.\s|[-*]\s)/.test(line)) {
        const result = parseList(lines, i);
        blocks.push(result.html);
        i = result.end;
        continue;
      }

      // Paragraph
      const paraLines = [];
      while (i < lines.length && lines[i].trim() !== '' && !/^(#{1,6}\s|```|>\s|[-*]{3,}$|\s*[-*]\s|\s*\d+\.\s)/.test(lines[i]) && !lines[i].includes('|')) {
        paraLines.push(lines[i]);
        i++;
      }
      if (paraLines.length) {
        blocks.push(`<p>${parseInline(paraLines.join(' '))}</p>`);
      }
    }

    return blocks.join('\n');
  }

  function renderInPlace(element, markdownString) {
    element.innerHTML = render(markdownString);
  }

  return { render, renderInPlace };
})();
