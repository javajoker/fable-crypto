# Routine tasks. Run `make help` for the list.
PY ?= python3
.PHONY: help check audit stablecoins site update serve

help:
	@echo "make check        recompute the model independently and compare with the workbook"
	@echo "make audit        compare the workbook's inputs with FRED and the Treasury"
	@echo "make stablecoins  refresh data/stablecoins.csv (locked USD) from DefiLlama"
	@echo "make site         rebuild the site's data files from the workbook and docs"
	@echo "make update       stablecoins + check + site: run after changing the workbook"
	@echo "make serve        serve the site at http://localhost:8765"
	@echo
	@echo "New quarter:  $(PY) scripts/fetch_inputs.py \"2026 Q4\"   then fill in the file it writes, then"
	@echo "              $(PY) scripts/add_quarter.py --from-json data/quarters/2026Q4.json && make update"

check:
	$(PY) scripts/check_model.py

audit:
	$(PY) scripts/fetch_inputs.py --audit

stablecoins:
	$(PY) scripts/fetch_stablecoins.py

site:
	$(PY) scripts/build_site.py

update: stablecoins check site

serve:
	$(PY) -m http.server 8765 --directory site
