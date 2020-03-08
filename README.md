# DNS record updater for NSD

## nsdで動的なレコード更新を行う
A/AAAA/TXT レコードの更新のみを対象にする

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

## LetsEncrypt(certbot)のTXTレコードによる更新に使うには
certbotでワイルドカード対応したい場合、TXTレコード更新が必要になります。<br>
1. あらかじめnsdのzoneファイルに、末尾ピリオド付きのFQDNで TXTレコードを登録しておきます。<br>
 _acme-challenge.ipmsg.org.  10  IN  TXT  dummy_value<br>

2. certbotでdns利用で更新リクエストを出すと TXTレコードにセットすべき値が表示されて待ち状態になるので、下記を実行します。<br>
 % nsd-upd.py _acme-challenge.ipmsg.org. txt=(value) /etc/nsd/zones/(zone-file)<br>
この後に、certbotの実行を継続すればOK。

3. 自動化するには upd-txt.sh といった名前で下記のような内容のscriptを作っておき、certbotの --manual-auth-hook に指定すればOK。<br>
 #!/bin/sh<br>
 /etc/nsd/nsd-upd.py _acme-challenge.$CERTBOT_DOMAIN. txt=$CERTBOT_VALIDATION /etc/nsd/zones/(zone-file)<br>
 
 （個人的にはそれ以外に、--expand --non-interactive --manual-public-ip-logging-ok --manual --preferred-challenges dns --keep-until-expiring --post-hook も指定）<br>

## 付記
zoneファイルが更新された場合、自動的に、serial番号を上げた上で、nsd-control reload を実行します。<br>
IPアドレスに変化が無い場合は、zoneファイルを変更しません。<br>
（nsd-control のパスは nsd-upd.py の先頭部分で適宜変更して下さい）

## 付記その２
nsd-reload.py を追加（confとzoneファイルの整合確認後にreloadするラッパーツール）。nsd-upd とは無関係。

## 作った理由
自宅環境のIPアドレスを反映したいため。<br>
普通は dynamic DNSサービスを使った方が手っ取り早いのですが、sshでsecureに更新＆他のサービスを介在させたくない、という理由から自作。
