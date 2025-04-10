import 'maplibre-gl/dist/maplibre-gl.css';
import { Map, Marker, Popup } from 'maplibre-gl';

import { createPoint, loadPoints, deletePoint, satelliteImageUrl } from './api';

const map = new Map({
  container: 'app',
  maxZoom: 18,
  center: [139.767125, 35.681236],
  style: {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution:
          "© OpenStreetMap contributors | Copernicus Sentinel data 2024' for Sentinel data",
      },
    },
    layers: [
      {
        id: 'osm',
        type: 'raster',
        source: 'osm',
      },
    ],
  },
});

// Marker関連の処理
const markers: Marker[] = [];
let isMarkerClicked = false;

const loadMarkers = async () => {
  // マップの現在の表示領域を取得
  const bounds = map.getBounds();
  const bbox: [number, number, number, number] = [
    bounds.getWest(),
    bounds.getSouth(),
    bounds.getEast(),
    bounds.getNorth()
  ];
  
  const points = await loadPoints(bbox);
  
  // points.featuresがundefinedまたは空の配列の場合の対策
  if (points.features && points.features.length > 0) {
    points.features.forEach((feature) => {
    const marker = new Marker()
      .setLngLat(feature.geometry.coordinates)
      .addTo(map);
    markers.push(marker);
  });
  }
};

const clearMarkers = () => {
  markers.forEach((marker) => marker.remove());
};

map.on('load', async () => {
  await loadMarkers();
});

map.on('click', async (e) => {
  if (isMarkerClicked) {
    // ピンのクリックであれば、以降の処理をしない
    isMarkerClicked = false;
    return;
  }

  if (!confirm('地点を作成しますか？')) return;

  const { lng, lat } = e.lngLat;
  await createPoint({ longitude: lng, latitude: lat });
  clearMarkers();
  await loadMarkers();
});
