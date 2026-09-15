from pathlib import Path

import json

p=Path(__file__).parents[1]/'index.html';s=p.read_text();d=json.loads((p.parent/'data/cities.json').read_text());a=s.index('const cities=');b=s.index(';const cfg=',a);s=s[:a]+'const cities='+json.dumps(d,separators=(',',':'))+s[b:];s=s.replace('<b>MODELLED:</b> comparative 0-10 indicators in this MVP are directional estimates','<b>OBSERVED:</b> city population and country price/internet context come from dated Eurostat series. <b>ESTIMATE:</b> cost and ease remain estimated; comparative scores are normalised',1);p.write_text(s)
