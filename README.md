# jwstascii-lambda-updater
![Travis (.com)](https://img.shields.io/travis/com/bweissinger/jwstascii-lambda-updater) [![Coverage Status](https://coveralls.io/repos/github/bweissinger/jwstascii-lambda-updater/badge.svg?branch=main)](https://coveralls.io/github/bweissinger/jwstascii-lambda-updater?branch=main)
<br>
AWS Lambda function for updating jwstascii.com.
This function probably isn't that useful for you... But feel free to browse.

## Flow
The lambda function completes the following steps:
1) Clone [jwstascii](https://github.com/bweissinger/jwstascii).
2) Scrapes an image, and associated info, from [webbtelescope.org](https://webbtelescope.org).
3) Creates ascii image from the downloaded photo.
4) Updates website files.
5) Push image to S3 Bucket.
6) Push changes to repo.
