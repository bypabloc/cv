import { db } from "astro:db";
import type { APIRoute } from "astro";
import { getAttributesByUsername } from "@/utils/getAttributesByUsername";

export const GET: APIRoute = async (context) => {
  try {
    console.log("Context:", context);
    const { request, params, props } = context;
    console.log("Request:", request);
    console.log("Params:", params);
    console.log("Props:", props);
    const url = new URL(request.url);
    const username = url.searchParams.get("username");

    if (!username) {
      return new Response(JSON.stringify({ error: "Username is required" }), {
        status: 422,
        headers: {
          "content-type": "application/json",
          // "cache-control": "public, s-maxage=60, stale-while-revalidate=25",
        },
      });
    }

    return new Response(JSON.stringify({ username }), {
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
        // "cache-control": "public, s-maxage=60, stale-while-revalidate=25",
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
