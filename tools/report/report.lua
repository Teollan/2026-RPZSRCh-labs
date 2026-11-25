-- pandoc filter for lab reports (used by build_report.py).

-- Captions as "Рисунок N – <caption>", numbered in order.
local figure_number = 0

local function file_exists(path)
  local f = io.open(path, 'rb')
  if f then f:close() end
  return f ~= nil
end

local function resource_exists(src)
  if file_exists(src) then return true end
  for _, dir in ipairs(PANDOC_STATE.resource_path or {}) do
    if file_exists(dir .. '/' .. src) then return true end
  end
  return false
end

-- An image whose file doesn't exist yet (a screenshot still to be taken) is
-- shown as a placeholder naming the file, so the report builds anyway. Once
-- the file is there, the next build shows the image.
local function placeholder_if_missing(fig)
  local missing
  fig.content = fig.content:walk{
    Image = function(img)
      if not resource_exists(img.src) then
        missing = img.src
        return pandoc.Strong{pandoc.Str('[Зображення буде додано: ' .. img.src .. ']')}
      end
    end,
  }
  return missing
end

function Figure(fig)
  placeholder_if_missing(fig)
  figure_number = figure_number + 1
  local prefix = pandoc.Inlines{
    pandoc.Str('Рисунок'), pandoc.Space(), pandoc.Str(tostring(figure_number)),
  }
  local long = fig.caption.long
  if #long > 0 and #pandoc.utils.stringify(long) > 0 then
    prefix:extend{pandoc.Space(), pandoc.Str('–'), pandoc.Space()}
    long[1].content = prefix .. long[1].content
  else
    fig.caption.long = pandoc.Blocks{pandoc.Plain(prefix)}
  end
  return fig
end

-- Syntax highlighting. pandoc 3.1's ODT writer doesn't highlight code, but its
-- HTML writer does (with the same highlighter, skylighting). So each code block
-- is rendered to HTML, and the token spans (<span class="kw">...) are turned
-- into ODT spans with the text styles Code_kw, Code_st, ... from the reference
-- document. A small spacer paragraph follows every block so neighbouring blocks
-- and the next paragraph don't run together.

-- Language names used in the reports that skylighting knows under another name.
local language_aliases = {
  docker = 'dockerfile',
  sh = 'bash',
  shell = 'bash',
  console = 'bash',
}

local function unescape_html(s)
  return (s:gsub('&lt;', '<'):gsub('&gt;', '>'):gsub('&quot;', '"')
           :gsub('&#39;', "'"):gsub('&amp;', '&'))
end

local function escape_xml(s)
  return (s:gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;'))
end

-- ODF collapses runs of spaces, so they have to be written as <text:s/>.
local function odt_text(s)
  s = escape_xml(s)
  s = s:gsub('\t', '<text:tab/>')
  s = s:gsub('  +', function(spaces)
    return ' <text:s text:c="' .. (#spaces - 1) .. '"/>'
  end)
  s = s:gsub('^ ', '<text:s/>')  -- a leading space would be dropped too
  return s
end

local function odt_line(html_line)
  -- Highlighted lines are wrapped once: <span id="cb1-3"><a ...></a> ... </span>.
  -- (Blocks in a language skylighting doesn't know come back as plain lines.)
  if html_line:match('^<span id="') then
    html_line = html_line:gsub('^<span id="[^"]*">', ''):gsub('<a [^>]*></a>', '')
    html_line = html_line:sub(1, -#'</span>' - 1)
  end

  local out, pos = {}, 1
  while true do
    local s, e, class, token = html_line:find('<span class="(%w+)">(.-)</span>', pos)
    if not s then break end
    if s > pos then
      table.insert(out, odt_text(unescape_html(html_line:sub(pos, s - 1))))
    end
    table.insert(out, '<text:span text:style-name="Code_' .. class .. '">'
                      .. odt_text(unescape_html(token)) .. '</text:span>')
    pos = e + 1
  end
  if pos <= #html_line then
    table.insert(out, odt_text(unescape_html(html_line:sub(pos))))
  end
  return table.concat(out)
end

function CodeBlock(block)
  local lang = block.classes[1]
  if lang and language_aliases[lang] then
    block.classes[1] = language_aliases[lang]
  end

  local html = pandoc.write(pandoc.Pandoc{block}, 'html')
  local code = html:match('<code[^>]*>(.*)</code>') or ''

  local paragraphs = {}
  for line in (code .. '\n'):gmatch('(.-)\n') do
    table.insert(paragraphs,
      '<text:p text:style-name="Preformatted_20_Text">' .. odt_line(line) .. '</text:p>')
  end
  table.insert(paragraphs, '<text:p text:style-name="Code_20_Spacer"/>')
  return pandoc.RawBlock('opendocument', table.concat(paragraphs, '\n'))
end
