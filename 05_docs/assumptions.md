# Assumptions

The choices behind the analysis, with the reasoning for each. These are what make the results defensible.

**LiDAR resolution.** OPW National LiDAR, 2 m grid, 2011 capture (CC-BY 4.0). This sets the floor on depth and height precision. Features smaller than about 2 m are not resolved.

**Building height source.** Height is the median of the normalised surface (DSM minus DTM) within each footprint. Median rather than mean, so chimneys, roof edges, and stray tall pixels do not inflate the wall height. Where a building had no LiDAR cover or a value under 2 m, height was set to a 6 m default (2 storeys). 60,954 buildings carry a real measured height; the rest use the default and sit outside the study reach.

**Floor-to-floor height.** 2.7 m, used to convert flood depth to storeys inundated (`ceil(depth / 2.7)`). A standard residential floor-to-floor figure for Irish housing.

**Ground-floor damage threshold.** 0.3 m. Depth above this over a footprint is treated as damaging ground-floor flooding, a common trigger for habitable-floor damage.

**Flood depth method.** Bathtub. The water surface was interpolated (TIN, linear) from ground elevations sampled every 25 m along the 1% flood-extent edge, then the DTM was subtracted and negatives dropped. It assumes a locally flat water surface tied to the extent edge, which suits a floodplain reach and is weaker on steep gradients. A small number of channel-edge cells show implausibly deep values (maximum 10.1 m), an artifact where a high bank elevation is interpolated over an adjacent low point. These affect under 2% of the flooded area and do not materially change per-building exposure.

**Study extent.** First pass over the lower and middle Dodder, the LiDAR-covered reach. The tiles cover 23% of the full catchment but 71% of the 1% flood extent, because the flood concentrates on the valley floor that was captured. The upstream uplands and the eastern suburbs (a gap in the OSM building download east of easting 720738) are outside this pass.

**Flood scenario.** 1% annual exceedance probability (the 100-year design flood), current scenario, from the OPW CFRAM Community-Scale River Flood Extents. The 10% and 0.1% events are available in the same GeoPackage for later runs.
