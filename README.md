# rabbithole
###### Send HTTP scrapers to Wonderland  
  
## about
This repository is to showcase techniques for occupying scrapers/spiders which might otherwise be up to malicious activities. Please be aware that these scripts were designed for entertainment purposes to spite the only traffic my site was getting (automated attacks from Chinese IP addresses), not as an actual web defense. Still, I hope that they will slow, frustrate, or crash attackers' poorly-written scrapers and provide a few good examples of cases to test when writing your own scraper.  
  
  
## techniques
Below is a list of the techniques I've tested and documented enough that I'm comfortable sharing them. Unless otherwise stated, expect the webserver to be `Apache 2.4` and the Python interpreter to be `Python 3.6` or later.  
  
### cgi-bin/junkstream.py  
This is a CGI script to supply an infinite stream of random garbage. By responding to URLs an attacker should not be accessing with the output of this endpoint, a webserver may occupy poorly written scrapers for a very long time, and even crash very poorly written scrapers when the system runs into memory constraints. Simply copy junkstream.py to your server's CGI directory and apply a rewrite rule such as the following, written in Apache's `mod_rewrite` syntax:  
```
RewriteEngine on  
RewriteRule /wp-admin/(.+)$ /cgi-bin/junkstream.py [NC,PT]  
```
For Apache users, remember to exempt this file from `mod_deflate`'s attention or the output pipe will fill and the CGI process will deadlock, sending no traffic to the client, but keeping the HTTP connection open.  
```
<FilesMatch /junkstream.py$>
        SetEnv no-gzip 1
</FilesMatch>
```
Remember to adjust the log directories, bitrate, etc in the CGI script. The default output type is `plain/text`, but you may wish to change this to `plain/xml` or something similar. (Remember to add a `<body>` tag if you do this!) You can also change the character encoding and various other features. Check the script itself for more detailed documentation!
