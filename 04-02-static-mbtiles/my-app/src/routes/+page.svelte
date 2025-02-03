<script lang="ts">
	import {
		MapLibre,
		NavigationControl,
		ScaleControl,
		GlobeControl,
		RasterTileSource,
		VectorTileSource,
		RasterLayer,
		CircleLayer
	} from 'svelte-maplibre-gl';
	import { page } from '$app/stores';

	const raster_url = "http://localhost:3000/" + 'raster/{z}/{x}/{y}.png';
	const vector_url = "http://localhost:3000/" + 'vector/{z}/{x}/{y}.pbf';
	console.log('vector_url:', vector_url);
</script>

<MapLibre
	class="h-[100vh] min-h-[300px]"
	style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
	zoom={3.5}
	center={{ lng: 137, lat: 36 }}
>
	<RasterTileSource tiles={[raster_url]} minzoom={0} maxzoom={6} tileSize={256}>
		<RasterLayer />
	</RasterTileSource>

	<VectorTileSource tiles={[vector_url]} minzoom={0} attribution="国土数値情報 - 学校データ">
		<CircleLayer sourceLayer="vector" paint={{ 'circle-radius': 5, 'circle-color': 'red' }} />
	</VectorTileSource>

	<!-- Add Control  -->
	<NavigationControl />
	<ScaleControl />
	<GlobeControl />
</MapLibre>
