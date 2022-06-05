## Steps of build and deploy :

- Build docker image on local machine

  ```
  docker build ./ -t docker.pkg.github.com/hkshopu/api_service/shop_api:[VERSION]
  ```

- Push the newly built docker image to Github

  ```
  docker push docker.pkg.github.com/hkshopu/api_service/shop_api:[VERSION]
  ```

  If this action failed, you should log in Github project with your account and secret token, like bellowing

  ```
  docker login docker.pkg.github.com -u garychang-times-transform -p [Your_Github_Token]
  ```

- SSH to the GCP vm, first stop and remove the current api container

  ```
  >sudo docker stop api
  >sudo docker rm api
  ```

- Last, run up the new docker image

  ```
  >sudo docker run -d -p 8000:80 --name api docker.pkg.github.com/hkshopu/api_service/shop_api:[VERSION]
  ```

  





