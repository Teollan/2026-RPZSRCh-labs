#!/usr/bin/env python3
"""Build a lab report: report.md -> report.odt.

    python3 tools/report/build_report.py lab1/report.md

The title page comes from title_template.odt (the lab2 stub, with the lab
number and topic as {{LAB}} / {{TOPIC}}). Both are read from the HTML title
block at the top of report.md, or given with --lab / --topic. Everything
before the first Markdown heading (that title block) is left out of the body.

The body is converted by pandoc using a reference document built here from
the template's styles, with body text styled like the lab assignments:
Times New Roman 14 pt, first-line indent 1.25 cm, bold headings. Code blocks
are syntax-highlighted by report.lua.

Export the PDF from LibreOffice (File > Export as PDF). Needs pandoc on PATH.
"""
import argparse
import copy
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
TITLE_TEMPLATE = HERE / 'title_template.odt'
# Roughly how many characters of the topic line fit on one line of the title page.
TOPIC_CHARS_PER_LINE = 42

NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
    'xlink': 'http://www.w3.org/1999/xlink',
    'svg': 'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0',
    'manifest': 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0',
    'loext': 'urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0',
}


def q(name):
    """'style:name' -> '{urn...style...}name'"""
    prefix, local = name.split(':')
    return f'{{{NS[prefix]}}}{local}'


def register_namespaces(xml_bytes):
    """Keep the document's own prefixes when ElementTree writes it back."""
    for prefix, uri in re.findall(rb'xmlns:([\w-]+)="([^"]+)"', xml_bytes):
        ET.register_namespace(prefix.decode(), uri.decode())


def parse(xml_bytes):
    register_namespaces(xml_bytes)
    return ET.fromstring(xml_bytes)


def serialize(root):
    return ET.tostring(root, encoding='UTF-8', xml_declaration=True)


# --- Body styles -------------------------------------------------------------

BODY_FONT = 'Times New Roman'
MONO_FONT = 'Liberation Mono'

# Styles pandoc uses for the body. Title-page styles (Standard, Heading,
# Heading_20_1, Heading_20_7) are deliberately not touched.
TEXT = (f'style:font-name="{BODY_FONT}" fo:font-size="14pt" '
        f'style:font-name-complex="{BODY_FONT}" style:font-size-complex="14pt" '
        'fo:language="uk" fo:country="UA"')
BODY_PARA = ('fo:text-indent="1.25cm" fo:margin-left="0cm" fo:margin-right="0cm" '
             'fo:margin-top="0cm" fo:margin-bottom="0.28cm" fo:line-height="108%" fo:text-align="start"')
HEADING_PARA = ('fo:text-indent="1.25cm" fo:margin-left="0cm" fo:margin-bottom="0.2cm" '
                'fo:keep-with-next="always" fo:text-align="start"')

STYLE_OVERRIDES = f'''
<style:style style:name="Text_20_body" style:display-name="Text body" style:family="paragraph" style:parent-style-name="Standard" style:class="text">
  <style:paragraph-properties {BODY_PARA}/>
  <style:text-properties {TEXT}/>
</style:style>
<style:style style:name="First_20_paragraph" style:display-name="First paragraph" style:family="paragraph" style:parent-style-name="Text_20_body" style:class="text"/>
<style:style style:name="Heading_20_2" style:display-name="Heading 2" style:family="paragraph" style:parent-style-name="Text_20_body" style:next-style-name="Text_20_body" style:default-outline-level="2" style:class="text">
  <style:paragraph-properties {HEADING_PARA} fo:margin-top="0.5cm"/>
  <style:text-properties {TEXT} fo:font-weight="bold" style:font-weight-complex="bold"/>
</style:style>
<style:style style:name="Heading_20_3" style:display-name="Heading 3" style:family="paragraph" style:parent-style-name="Text_20_body" style:next-style-name="Text_20_body" style:default-outline-level="3" style:class="text">
  <style:paragraph-properties {HEADING_PARA} fo:margin-top="0.4cm"/>
  <style:text-properties {TEXT} fo:font-weight="bold" style:font-weight-complex="bold"/>
</style:style>
<style:style style:name="Heading_20_4" style:display-name="Heading 4" style:family="paragraph" style:parent-style-name="Text_20_body" style:next-style-name="Text_20_body" style:default-outline-level="4" style:class="text">
  <style:paragraph-properties {HEADING_PARA} fo:margin-top="0.3cm"/>
  <style:text-properties {TEXT} fo:font-style="italic" style:font-style-complex="italic"/>
</style:style>
<style:style style:name="Preformatted_20_Text" style:display-name="Preformatted Text" style:family="paragraph" style:parent-style-name="Standard" style:class="html">
  <style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0cm" fo:text-indent="0cm" fo:line-height="100%" fo:background-color="#f3f3f3" fo:padding-left="0.15cm" fo:padding-right="0.15cm"/>
  <style:text-properties style:font-name="{MONO_FONT}" fo:font-size="10pt" style:font-name-complex="{MONO_FONT}" style:font-size-complex="10pt"/>
</style:style>
<style:style style:name="Source_Text" style:display-name="Source Text" style:family="text">
  <style:text-properties fo:font-weight="bold" style:font-weight-complex="bold"/>
</style:style>
<style:style style:name="Code_20_Spacer" style:display-name="Code Spacer" style:family="paragraph" style:parent-style-name="Standard" style:class="text">
  <style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0cm" fo:text-indent="0cm" fo:line-height="100%"/>
  <style:text-properties fo:font-size="8pt" style:font-size-complex="8pt"/>
</style:style>
<style:style style:name="Figure" style:family="paragraph" style:parent-style-name="Standard" style:class="extra">
  <style:paragraph-properties fo:text-align="center" fo:text-indent="0cm" fo:margin-top="0.2cm" fo:margin-bottom="0cm" fo:keep-with-next="always"/>
</style:style>
<style:style style:name="FigureWithCaption" style:family="paragraph" style:parent-style-name="Figure" style:class="extra"/>
<style:style style:name="FigureCaption" style:family="paragraph" style:parent-style-name="Text_20_body" style:class="extra">
  <style:paragraph-properties fo:text-align="center" fo:text-indent="0cm" fo:margin-top="0.1cm" fo:margin-bottom="0.3cm"/>
  <style:text-properties {TEXT}/>
</style:style>
<style:style style:name="Table_20_Contents" style:display-name="Table Contents" style:family="paragraph" style:parent-style-name="Text_20_body" style:class="extra">
  <style:paragraph-properties fo:text-indent="0cm" fo:margin-bottom="0cm"/>
</style:style>
<style:style style:name="Table_20_Heading" style:display-name="Table Heading" style:family="paragraph" style:parent-style-name="Table_20_Contents" style:class="extra">
  <style:text-properties fo:font-weight="bold" style:font-weight-complex="bold"/>
</style:style>
'''

# Colours for highlighted code (pandoc's default "pygments" theme), keyed by
# the token classes pandoc's highlighter produces. report.lua uses the text
# styles Code_<class>.
CODE_TOKENS = {
    'kw': ('#007020', 'bold'),   # keyword
    'cf': ('#007020', 'bold'),   # control flow
    'dt': ('#902000', None),     # data type
    'dv': ('#40a070', None),     # decimal value
    'bn': ('#40a070', None),     # base-n number
    'fl': ('#40a070', None),     # float
    'cn': ('#880000', None),     # constant
    'ch': ('#4070a0', None),     # char
    'sc': ('#4070a0', None),     # special char
    'st': ('#4070a0', None),     # string
    'vs': ('#4070a0', None),     # verbatim string
    'ss': ('#bb6688', None),     # special string
    'im': ('#007020', None),     # import
    'co': ('#60a0b0', 'italic'), # comment
    'do': ('#ba2121', 'italic'), # documentation
    'an': ('#60a0b0', 'bold-italic'),  # annotation
    'cv': ('#60a0b0', 'bold-italic'),  # comment var
    'in': ('#60a0b0', 'bold-italic'),  # information
    'wa': ('#60a0b0', 'bold-italic'),  # warning
    'ot': ('#007020', None),     # other
    'fu': ('#06287e', None),     # function
    'va': ('#19177c', None),     # variable
    'op': ('#666666', None),     # operator
    'bu': ('#007020', None),     # built-in
    'ex': ('#007020', None),     # extension
    'pp': ('#bc7a00', None),     # preprocessor
    'at': ('#7d9029', None),     # attribute
    'al': ('#ff0000', 'bold'),   # alert
    'er': ('#ff0000', 'bold'),   # error
}


def code_token_styles():
    styles = []
    for cls, (color, look) in CODE_TOKENS.items():
        props = f'fo:color="{color}"'
        if look in ('bold', 'bold-italic'):
            props += ' fo:font-weight="bold" style:font-weight-complex="bold"'
        if look in ('italic', 'bold-italic'):
            props += ' fo:font-style="italic" style:font-style-complex="italic"'
        styles.append(f'<style:style style:name="Code_{cls}" style:family="text">'
                      f'<style:text-properties {props}/></style:style>')
    return '\n'.join(styles)


FONT_DECLS = f'''
<style:font-face style:name="{BODY_FONT}" svg:font-family="&apos;{BODY_FONT}&apos;" style:font-family-generic="roman" style:font-pitch="variable"/>
<style:font-face style:name="{MONO_FONT}" svg:font-family="&apos;{MONO_FONT}&apos;" style:font-family-generic="modern" style:font-pitch="fixed"/>
'''


def fragment(xml):
    """Parse a snippet of ODF elements using the namespace prefixes above."""
    decls = ' '.join(f'xmlns:{p}="{u}"' for p, u in NS.items())
    return list(ET.fromstring(f'<root {decls}>{xml}</root>'))


def build_reference(pandoc_ref: Path, out: Path):
    """Reference doc = the title template's styles (page layout, title-page
    styles) + pandoc's own styles it lacks + the body overrides above."""
    with zipfile.ZipFile(TITLE_TEMPLATE) as z:
        styles = parse(z.read('styles.xml'))
    with zipfile.ZipFile(pandoc_ref) as z:
        pandoc_styles = parse(z.read('styles.xml'))

    office_styles = styles.find(q('office:styles'))
    by_name = {s.get(q('style:name')): s for s in office_styles if s.get(q('style:name'))}

    # Add pandoc styles the template doesn't have (lists, quotations, definitions...).
    for s in pandoc_styles.find(q('office:styles')):
        name = s.get(q('style:name'))
        if s.tag == q('style:style') and name and name not in by_name:
            office_styles.append(copy.deepcopy(s))
            by_name[name] = office_styles[-1]

    # Replace or add the body styles.
    for s in fragment(STYLE_OVERRIDES + code_token_styles()):
        name = s.get(q('style:name'))
        if name in by_name:
            office_styles.remove(by_name[name])
        office_styles.append(s)
        by_name[name] = s

    decls = styles.find(q('office:font-face-decls'))
    have = {f.get(q('style:name')) for f in decls}
    for f in fragment(FONT_DECLS):
        if f.get(q('style:name')) not in have:
            decls.append(f)

    with zipfile.ZipFile(pandoc_ref) as zin, zipfile.ZipFile(out, 'w') as zout:
        for info in zin.infolist():
            data = serialize(styles) if info.filename == 'styles.xml' else zin.read(info.filename)
            zout.writestr(info, data)


# --- Images --------------------------------------------------------------------

def to_cm(length):
    value, unit = re.fullmatch(r'([\d.]+)(cm|mm|in|pt)', length).groups()
    return float(value) * {'cm': 1, 'mm': 0.1, 'in': 2.54, 'pt': 2.54 / 72}[unit]


def text_area(odt):
    """(width, height) in cm of the page's text area, from the template's page layout."""
    with zipfile.ZipFile(odt) as z:
        styles = parse(z.read('styles.xml'))
    for props in styles.iter(q('style:page-layout-properties')):
        if props.get(q('fo:page-width')):
            get = lambda a: to_cm(props.get(q(a), '0cm'))
            return (get('fo:page-width') - get('fo:margin-left') - get('fo:margin-right'),
                    get('fo:page-height') - get('fo:margin-top') - get('fo:margin-bottom'))
    return 16.0, 24.0


def fit_images(content, area):
    """pandoc sizes images at 72 dpi, so screenshots come out far too big.
    Scale every image down to the text width (and at most ~70% of the text
    height, leaving room for the caption), and centre it inline."""
    max_w, max_h = area[0], area[1] * 0.7
    for frame in content.iter(q('draw:frame')):
        w, h = frame.get(q('svg:width')), frame.get(q('svg:height'))
        if not w or not h:
            continue
        w, h = to_cm(w), to_cm(h)
        scale = min(1.0, max_w / w, max_h / h)
        frame.set(q('svg:width'), f'{w * scale:.3f}cm')
        frame.set(q('svg:height'), f'{h * scale:.3f}cm')
        frame.set(q('text:anchor-type'), 'as-char')


# --- Title page ----------------------------------------------------------------

def merge_title(body_odt: Path, out: Path, lab: str, topic: str):
    """Put the filled-in title page in front of pandoc's body."""
    with zipfile.ZipFile(TITLE_TEMPLATE) as z:
        tcontent = z.read('content.xml').decode()
        pictures = {n: z.read(n) for n in z.namelist() if n.startswith('Pictures/')}
    for key, value in (('{{LAB}}', lab), ('{{TOPIC}}', topic)):
        assert tcontent.count(key) == 1, key
        tcontent = tcontent.replace(key, escape(value))
    title = parse(tcontent.encode())

    with zipfile.ZipFile(body_odt) as z:
        body_files = {i.filename: z.read(i.filename) for i in z.infolist()}
        body_infos = z.infolist()
    body = parse(body_files['content.xml'])

    # Rename the title page's automatic styles so they can't clash with pandoc's.
    t_auto = title.find(q('office:automatic-styles'))
    renames = {s.get(q('style:name')): 'Title' + s.get(q('style:name')) for s in t_auto}
    for el in title.iter():
        for attr, value in list(el.attrib.items()):
            if attr.endswith('}style-name') and value in renames:
                el.set(attr, renames[value])
    for s in t_auto:
        s.set(q('style:name'), renames[s.get(q('style:name'))])

    # Page break after the "Київ 2026" line, which ends the title page.
    t_text = title.find(q('office:body')).find(q('office:text'))
    paras = [p for p in t_text if p.tag == q('text:p')]
    last_line = next(p for p in reversed(paras) if ''.join(p.itertext()).strip())
    style = t_auto.find(f"style:style[@style:name='{last_line.get(q('text:style-name'))}']", NS)
    props = style.find(q('style:paragraph-properties'))
    if props is None:
        props = ET.SubElement(style, q('style:paragraph-properties'))
    props.set(q('fo:break-after'), 'page')
    # Drop everything after it (empty paragraphs that would make a blank page).
    idx = list(t_text).index(last_line)
    for el in list(t_text)[idx + 1:]:
        t_text.remove(el)

    # The stub is laid out for a one-line topic. For each extra line a longer
    # topic needs, drop one of the empty spacer lines above "Київ 2026", so the
    # title page still fits on one page.
    extra_lines = -(-len(f'Тема: «{topic}»') // TOPIC_CHARS_PER_LINE) - 1
    for _ in range(extra_lines):
        idx = list(t_text).index(last_line)
        before = t_text[idx - 1]
        if before.tag == q('text:p') and not ''.join(before.itertext()).strip():
            t_text.remove(before)

    fit_images(body, text_area(TITLE_TEMPLATE))

    b_auto = body.find(q('office:automatic-styles'))
    for s in t_auto:
        b_auto.append(s)

    b_decls = body.find(q('office:font-face-decls'))
    t_decls = title.find(q('office:font-face-decls'))
    if b_decls is not None and t_decls is not None:
        have = {f.get(q('style:name')) for f in b_decls}
        for f in t_decls:
            if f.get(q('style:name')) not in have:
                b_decls.append(f)

    b_text = body.find(q('office:body')).find(q('office:text'))
    title_elements = [el for el in t_text if el.tag != q('text:sequence-decls')]
    insert_at = sum(1 for el in b_text if el.tag == q('text:sequence-decls'))
    for i, el in enumerate(title_elements):
        b_text.insert(insert_at + i, el)

    # Register the title page's picture(s) in the manifest.
    manifest = parse(body_files['META-INF/manifest.xml'])
    for name in pictures:
        entry = ET.SubElement(manifest, q('manifest:file-entry'))
        entry.set(q('manifest:full-path'), name)
        entry.set(q('manifest:media-type'), 'image/png' if name.endswith('.png') else '')

    with zipfile.ZipFile(out, 'w') as zout:
        for info in body_infos:
            name = info.filename
            data = body_files[name]
            if name == 'content.xml':
                data = serialize(body)
            elif name == 'META-INF/manifest.xml':
                data = serialize(manifest)
            mode = zipfile.ZIP_STORED if name == 'mimetype' else zipfile.ZIP_DEFLATED
            zout.writestr(info, data, compress_type=mode)
        for name, data in pictures.items():
            zout.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)


# --- Markdown ------------------------------------------------------------------

def split_markdown(text):
    """Return (lab, topic, body). The body starts at the first heading."""
    m = re.search(r'^#{1,6} ', text, re.M)
    if not m:
        sys.exit('report.md has no Markdown heading to start the body from')
    head, body = text[:m.start()], text[m.start():]
    head = re.sub(r'<[^>]+>', ' ', head)  # drop the HTML tags of the title block
    lab = re.search(r'лабораторної роботи\s*№?\s*(\d+)', head)
    # The topic is the first quoted text after the lab number.
    topic = re.search(r'["«“]([^"»”]+)["»”]', head[lab.end():]) if lab else None
    return (lab.group(1) if lab else None), (topic.group(1).strip() if topic else None), body


def built_by_us(odt):
    """Reports from this script carry the renamed title styles (TitleP1...)."""
    try:
        with zipfile.ZipFile(odt) as z:
            return b'style:name="TitleP1"' in z.read('content.xml')
    except (zipfile.BadZipFile, KeyError):
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('markdown', type=Path, help='path to report.md')
    ap.add_argument('--lab', help='lab number (default: from the title block in report.md)')
    ap.add_argument('--topic', help='lab topic (default: from the title block in report.md)')
    args = ap.parse_args()

    md = args.markdown.resolve()
    lab, topic, body = split_markdown(md.read_text(encoding='utf-8'))
    lab, topic = args.lab or lab, args.topic or topic
    if not lab or not topic:
        sys.exit('could not find the lab number or topic in report.md; pass --lab and --topic')

    if not shutil.which('pandoc'):
        sys.exit('pandoc not found on PATH')

    out_odt = md.with_suffix('.odt')
    if out_odt.exists() and not built_by_us(out_odt):
        sys.exit(f'{out_odt} exists and was not made by this script; move it away first')

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'body.md').write_text(body, encoding='utf-8')
        subprocess.run(['pandoc', '-o', tmp / 'pandoc_ref.odt', '--print-default-data-file', 'reference.odt'], check=True)
        build_reference(tmp / 'pandoc_ref.odt', tmp / 'reference.odt')
        subprocess.run([
            # -smart: keep "--" and quotes as written (e.g. --symlink-install).
            'pandoc', tmp / 'body.md', '-f', 'markdown-smart', '-t', 'odt',
            '--lua-filter', HERE / 'report.lua',
            '--reference-doc', tmp / 'reference.odt',
            '--resource-path', md.parent,
            '-M', 'lang=uk-UA',
            '-o', tmp / 'body.odt',
        ], check=True)
        merge_title(tmp / 'body.odt', out_odt, lab, topic)
        print(f'written {out_odt}')


if __name__ == '__main__':
    main()
