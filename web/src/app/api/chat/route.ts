import { OpenAI } from 'openai';
import { QdrantClient } from '@qdrant/js-client-rest';
import { NextResponse } from 'next/server';

// Initialize Clients
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const qdrant = new QdrantClient({
  url: process.env.QDRANT_URL,
  apiKey: process.env.QDRANT_API_KEY,
});

const COLLECTION_NAME = 'engineering_standards'; // Must match your existing collection

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { question } = body;

    if (!question) {
      return NextResponse.json({ error: 'Question is required' }, { status: 400 });
    }

    // 1. Generate Embedding for the user's question
    const embeddingResponse = await openai.embeddings.create({
      model: 'text-embedding-3-large', // Ensure this matches your Python ingestion model
      input: question,
    });

    const queryVector = embeddingResponse.data[0].embedding;

    // 2. Search in Qdrant Vector DB
    const searchResults = await qdrant.search(COLLECTION_NAME, {
      vector: queryVector,
      limit: 5,
      with_payload: true,
    });

    // 3. Construct Context from Search Results
    const context = searchResults
      .map((hit: any) => `Source: ${hit.payload?.metadata?.file_name || 'Unknown'}\nContent: ${hit.payload?.text || ''}`)
      .join('\n\n---\n\n');

    const systemPrompt = `You are an expert Engineering Consultant for electrical standards (IS 3218, etc.).
Answer the user's question based strictly on the provided context below.
If the answer is not in the context, say "I cannot find this information in the standards."
Include references to the specific documents if available.

Context:
${context}`;

    // 4. Generate Answer using LLM (GPT-4 or GPT-3.5)
    // Using gpt-4o or gpt-4-turbo for best results
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o', 
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: question },
      ],
      temperature: 0.1,
    });

    const answer = completion.choices[0].message.content;

    // 5. Return Response
    return NextResponse.json({
      answer: answer,
      sources: searchResults.map((hit: any) => ({
        text: hit.payload?.text,
        metadata: hit.payload?.metadata,
        score: hit.score,
      })),
    });

  } catch (error: any) {
    console.error('API Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
