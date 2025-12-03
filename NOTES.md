## Update of the qlever endpoitn with the latest set of queries
https://github.com/earth-metabolome-initiative/metrin-kg/discussions/3#discussioncomment-15119004


java -Dlog4j.configuration=file:./log4j.properties \
  -jar target/sparql-examples-utils-2.0.10-uber.jar \
  convert --input-directory=../sparql-examples/examples -p METRINKG -f ttl > test.ttl

```bash
java -Dlog4j.configuration=file:./log4j.properties \
  -jar target/sparql-examples-utils-2.0.10-uber.jar \
  convert --input-directory=../sparql-examples/examples -p METRINKG -f ttl | pigz > examples_METRINKG-v0.1.ttl.gz
```

### Void generator

```bash
java -jar target/void-generator*-uber.jar -r "https://kg.earthmetabolome.org/metrin/api/" --void-file void_METRINKG-v0.1.ttl --iri-of-void https://kg.earthmetabolome.org/metrin/api/.well-known/void# --max-concurrency 1 -f --optimize-for Qlever
pigz void_METRINKG-v0.1.ttl
```

### Qlever endpoint update



You need to have [qlever-control](https://github.com/qlever-dev/qlever-control) installed.

```bash
pip install qlever
```

In case you have it installed but need to force update

```bash
pip install qlever -U
```

Create a directory for the kg to be served and navigate to it.
For example

```bash
mkdir metrin-kg
cd metrinkg-kg
```

Fetch the appropriate Qleverfile.
For ex (METRINKG)





qlever get-data
qlever index --overwrite-existing --parallel-parsing false --stxxl-memory 32G (can take a bunch of time)
qlever stop (to kill current instance)
qlever start