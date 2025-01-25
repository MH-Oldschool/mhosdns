# Portable MH Oldschool DNS Server

If you're experiencing issues with our public DNS server, you can use this software to set up a local DNS server pre-configured to connect to all of our infrastructure, including game and DLC servers. Simply launch the app, start the server, and set your DNS to the local IP address displayed on your screen.

![Screenshot](.github/screenshot.png)

## How to build?

Install all the dependencies listed in `requirements.txt`, then install `pyinstaller` and run `pyinstaller main.spec`. Alternatively, you can download a precompiled version from the Releases section.
