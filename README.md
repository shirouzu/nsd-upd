# DNS record updater for NSD

## nsdで動的なレコード更新を行う
A/AAAA レコードの更新のみを対象にする

## 特徴
ssh 経由で更新する場合、'src' を指定すると、接続元IPアドレスを設定可能

## 前提
1. ssh 経由でアップデートすることを想定
2. /etc/nsd に nsd-upd.py を置き、chmod 755 されている。
3. nsd-control が /usr/sbin に存在する（違う場合は nsd-upd.py の RELOAD_CMD= を変更）
4. 書き換えたいレコードが存在する（新規追加はしません）

## 使い方
例えば、dns.example.jp で nsd を動かしており、/etc/nsd/zones/example.jp に zoneファイルがある場合に、targ-name IN A 1.0.0.1 というレコードを 1.0.0.2 に更新したい場合は下記の通り。<br>
% ssh dns.example.jp /etc/nsd/nsd-upd.py targ-name 1.0.0.2 /etc/nsd/zones/example.jp

また、sshの接続元アドレスを指定したい場合、IPアドレスの代わりに 'src' を指定します。<br>
% ssh dns.example.jp /etc/nsd/nsd-upd.py targ-name src /etc/nsd/zones/example.jp

## 付記
zoneファイルが更新された場合、自動的に、serial番号を上げた上で、nsd-control reload を実行します。<br>
IPアドレスに変化が無い場合は、zoneファイルを変更しません。<br>
（nsd-control のパスは nsd-upd.py の先頭部分で適宜変更して下さい）

## 作った理由
自宅環境のIPアドレスを反映したいため。<br>
普通は dynamic DNSサービスを使った方が手っ取り早いのですが、sshでsecureに更新＆他のサービスを介在させたくない、という理由から自作。
