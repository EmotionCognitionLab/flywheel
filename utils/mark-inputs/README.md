Provides a basic web interface that allows you to mark Flywheel analysis outputs so that they can be used as inputs to an SDK-based gear.

To run the server:

```
cd server
pipenv shell
cd fw-mark-inputs
chalice local
```

To deploy the server (assuming that you already have your AWS credentials set up):

```
cd server
pipenv shell
cd fw-mark-inputs
chalice deploy
```

This will deploy your code to AWS Lambda, create an API Gateway interface for it and give you the URL to the created API.

To run the client you first need to install the relevant node modules:

```
cd client
npm install
```
Once that's done you're ready to run the client locally in dev mode:

```npm run serve```

To build a client distribution:
```
cd client
npm run build
```

The client distribution will be put in the 'dist' directory. It is totally static and can be run from any http server - just copy the contents of the dist directory to the server's document root.

For more information on the server framework, see [Chalice](https://github.com/aws/chalice). For the client framework, see  [Vue](https://vuejs.org/v2/guide/).