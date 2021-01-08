
We bundle the tested .jar binaries from Tika right into the docker image.
The python tika integration expects the .jar file in /usr/tmp/ , so we'll copy it there 
(see Dockerfile)

See:  https://tika.apache.org/download.html

