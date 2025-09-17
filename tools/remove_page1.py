import xml.etree.ElementTree as ET

tree = ET.parse('sitemap_20250912_094425.xml')
root = tree.getroot()

ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

urls_to_remove = []
for url in root.findall('ns:url', ns):
    loc = url.find('ns:loc', ns)
    if loc is not None and loc.text is not None and loc.text.endswith('&page=1'):
        urls_to_remove.append(url)

for url in urls_to_remove:
    root.remove(url)

tree.write('sitemap_20250912_094425.xml', encoding='utf-8', xml_declaration=True)