## MGKDB Web

Some instructions for myself at this point in the dev process

To set up the dev environment navigate to ```App/``` and build the image

```docker build -t mgkdb:latest .```

Then run the environment

```docker run --name mgkdb -d -p 80:80 mgkdb```

The app is then accessible at ```127.0.0.1``` due to the port forwarding configured