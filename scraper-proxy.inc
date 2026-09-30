# Shared proxy settings for the scraper container (included by nginx.conf).
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header Accept-Encoding "";   # sub_filter needs uncompressed HTML
proxy_read_timeout 600s;
proxy_buffering off;

# The original UI ships htmx 1.9.6, which drops the job table rows when /jobs returns
# <tbody> + an OOB pagination <div>. htmx's useTemplateFragments config fixes the parsing.
sub_filter_once on;
sub_filter '</head>' '<meta name="htmx-config" content=\'{"useTemplateFragments":true}\'></head>';
