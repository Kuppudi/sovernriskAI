# World map outlines

`world-countries.json` contains only geometry, display names, and country identifiers. Economic values come from the application API, never from this file.

Source: [Natural Earth v5.1.2, 1:110m country outlines](https://github.com/nvkelso/natural-earth-vector/blob/v5.1.2/geojson/ne_110m_admin_0_countries.geojson).

[Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/): public domain. No runtime map account or external tile service is required.

The local copy omits Antarctica and unused source attributes. It chooses the first usable three-letter identifier from `WB_A3`, `ISO_A3_EH`, `ISO_A3`, then `ADM0_A3`. The original geometry is unchanged. Some small countries are absent at this map scale; the loaded-country buttons remain an alternative way to select them. Outlines are a visual base layer, separate from World Bank country metadata and data availability.
