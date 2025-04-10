const API_HOST = 'http://localhost:3000'; // 環境変数から注入するとなお良い

const createPoint = async (data: { longitude: number; latitude: number }) => {
  await fetch(`${API_HOST}/points`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
};

const deletePoint = async (id: string) => {
  await fetch(`${API_HOST}/points/${id}`, {
    method: 'DELETE',
  });
};

type PointsResponse = {
  type: 'FeatureCollection';
  features: {
    type: 'Feature';
    geometry: {
      type: 'Point';
      coordinates: [number, number];
    };
    properties: {
      id: string;
    };
  }[];
};

const loadPoints = async (
  bbox?: [number, number, number, number],
): Promise<PointsResponse> => {
  // デフォルトのbbox値（東京周辺）を設定
  const defaultBbox: [number, number, number, number] = [
    139.5, 35.5, 140.0, 36.0,
  ];

  // bboxパラメータが指定されていない場合はデフォルト値を使用
  const bboxToUse = bbox || defaultBbox;

  const response = await fetch(
    `${API_HOST}/points?bbox=${bboxToUse.join(',')}`,
  );
  const data = await response.json();
  return data;
};

const satelliteImageUrl = (id: string, maxSize: number = 256) =>
  `${API_HOST}/points/${id}/satellite.jpg?max_size=${maxSize}`;

export { createPoint, deletePoint, loadPoints, satelliteImageUrl };
