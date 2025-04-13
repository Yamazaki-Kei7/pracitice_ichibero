#!/bin/bash
set -e

# PostgreSQLが起動するまで待機
until pg_isready -U postgres; do
  echo "PostgreSQLが起動するのを待っています..."
  sleep 1
done

# pg_hba.confファイルのあるディレクトリを検索
PG_HBA_PATH=$(find /etc/postgresql -name pg_hba.conf)

if [ -z "$PG_HBA_PATH" ]; then
  echo "pg_hba.confファイルが見つかりませんでした"
  exit 1
fi

echo "pg_hba.confファイルを編集します: $PG_HBA_PATH"

# バックアップを作成
cp $PG_HBA_PATH ${PG_HBA_PATH}.bak

# peer認証をmd5に変更
sed -i 's/local.*all.*postgres.*peer/local   all             postgres                                md5/g' $PG_HBA_PATH

# Unix socketでのすべての接続に対する認証設定を追加（既存の設定を置き換え）
sed -i 's/local.*all.*all.*peer/local   all             all                                     md5/g' $PG_HBA_PATH

echo "pg_hba.confファイルを更新しました"

# PostgreSQLを再起動して設定を反映
echo "PostgreSQLを再起動します"
pg_ctl -D $(find /var/lib/postgresql -name main -type d) reload

echo "認証設定の変更が完了しました"

