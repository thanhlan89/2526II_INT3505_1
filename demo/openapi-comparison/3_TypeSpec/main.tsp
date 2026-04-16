import "@typespec/http";
import "@typespec/openapi3";

using TypeSpec.Http;

@service({ title: "Library Management API", version: "1.0.0" })
namespace Library;

model Book {
  id?: string;
  title: string;
  author: string;
}

@route("/books")
interface Books {
  @get list(): Book[];
  @post create(@body book: Book): { @statusCode _: 201 };
}