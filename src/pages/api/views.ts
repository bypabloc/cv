// src/api/views.ts
import { db, Views } from "astro:db";
import type { APIRoute } from "astro";

export const GET: APIRoute = async ({ request }) => {
  try {
    const basics = await db.select().from(Views).all();

    return new Response(JSON.stringify({ basics }), {
      status: 200,
      headers: {
        "content-type": "application/json",
        "cache-control": "public, s-maxage=60, stale-while-revalidate=25",
      },
    });
  } catch (error) {
    console.log("Error:", error);
    return new Response(JSON.stringify({ error }), {
      status: 500,
      headers: {
        "content-type": "application/json",
        "cache-control": "public, s-maxage=60, stale-while-revalidate=25",
      },
    });
  }
};

export const POST: APIRoute = ({ request }) => {
  return new Response(
    JSON.stringify({
      message: "This was a POST!",
    })
  );
};
