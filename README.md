## MGKDB Web

Some instructions for myself at this point in the dev process

To run the app navigate to top level directory and run

```docker-compose up```

In order for the App container to connect to the remote DB an ssh tunnel has to be established. Once the container is up, access it via

```docker exec -it app /bin/bash```

Map local port 27017 to remote db by running the following command

```ssh -4 -i .ssh/nersc -f gsalazar@cori.nersc.gov -L 27017:mongodb03.nersc.gov:27017 -N````

Ensure this is the port being used in the ```MONGO_URL``` variable stored in the ```.env``` file.

Access MySQL DB inside running docker container

``` mysql -u username -p -h 172.20.0.0.3 -P 3306```