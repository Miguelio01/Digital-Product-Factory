Guía: Creación de Agente IA para Marketing con NestJS
¡Excelente iniciativa, colega! Construir un "mini JARVIS" para marketing digital es un proyecto ambicioso pero totalmente viable con el stack tecnológico adecuado. Para que esto funcione a nivel profesional, pero accesible para un perfil junior, utilizaremos NestJS (backend robusto), LangChain.js (orquestación de IA) y LangGraph (para el comportamiento agéntico y auto-prompting).
Aquí tienes la guía directa, paso a paso y con código, basada en las mejores prácticas documentadas.
Arquitectura del Sistema
Para lograr un sistema que hable, escuche, genere imágenes y cree documentos Markdown (.md), necesitamos integrar:
1. Ingesta de Conocimiento (RAG): Procesar tus PDFs de marketing.
2. Cerebro Agéntico (LangGraph): Un grafo que decida cuándo investigar, cuándo escribir y cuándo generar imágenes.
3. Interfaz de Voz: Conversión de Audio a Texto (STT) y Texto a Audio (TTS).
--------------------------------------------------------------------------------
Paso 1: Configuración del Proyecto (NestJS)
Primero, iniciamos el proyecto e instalamos las dependencias clave para IA, manejo de archivos y bases de datos vectoriales.
# Iniciar proyecto NestJS
nest new jarvis-marketing
cd jarvis-marketing

# Instalar dependencias base de LangChain y OpenAI
npm install @langchain/openai @langchain/core @langchain/community langchain
npm install pdf-parse zod
# Para manejo de audio y archivos
npm install multer fluent-ffmpeg
Paso 2: El Sistema RAG (Tu Base de Conocimiento)
Necesitamos que el agente lea tus PDFs. Crearemos un servicio que cargue el PDF, lo divida en fragmentos (chunks) y lo guarde en una base vectorial (usaremos una en memoria para este ejemplo, pero en producción usarías Qdrant o Supabase).
Archivo: src/rag/rag.service.ts
import { Injectable } from '@nestjs/common';
import { PDFLoader } from '@langchain/community/document_loaders/fs/pdf';
import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter';
import { MemoryVectorStore } from 'langchain/vectorstores/memory';
import { OpenAIEmbeddings } from '@langchain/openai';

@Injectable()
export class RagService {
  private vectorStore: MemoryVectorStore;

  // 1. Cargar y procesar el PDF
  async ingestPdf(filePath: string) {
    // Cargamos el PDF
    const loader = new PDFLoader(filePath);
    const docs = await loader.load();

    // Dividimos en trozos para que quepan en el contexto del LLM [4]
    const splitter = new RecursiveCharacterTextSplitter({
      chunkSize: 1000,
      chunkOverlap: 200,
    });
    const splitDocs = await splitter.splitDocuments(docs);

    // Creamos los embeddings (representación matemática del texto)
    this.vectorStore = await MemoryVectorStore.fromDocuments(
      splitDocs,
      new OpenAIEmbeddings()
    );
    console.log('Base de conocimiento actualizada.');
  }

  // 2. Método para recuperar contexto
  async retrieveContext(query: string) {
    if (!this.vectorStore) return '';
    // Buscamos los 3 fragmentos más relevantes
    const results = await this.vectorStore.similaritySearch(query, 3);
    return results.map((doc) => doc.pageContent).join('\n\n');
  }
}
Paso 3: El Agente "JARVIS" con LangGraph
Aquí es donde ocurre la magia. No usaremos una simple cadena lineal; usaremos un Grafo de Estado (StateGraph). Esto permite que el agente tenga "memoria" y decida pasos. Implementaremos un flujo que incluye "auto-prompting" (mejorar su propia instrucción antes de ejecutarla).
Concepto de Auto-Prompting: El agente recibe tu petición, la analiza, y genera un prompt interno más detallado y técnico basado en su conocimiento de marketing antes de generar el resultado final.
Archivo: src/agent/agent.service.ts
import { Injectable } from '@nestjs/common';
import { StateGraph, END, START, Annotation } from '@langchain/langgraph';
import { ChatOpenAI } from '@langchain/openai';
import { SystemMessage, HumanMessage } from '@langchain/core/messages';
import { RagService } from '../rag/rag.service';
import { DallEAPIWrapper } from '@langchain/openai'; // Para imágenes

// Definimos el estado del grafo [7]
const AgentState = Annotation.Root({
  messages: Annotation<any[]>({
    reducer: (x, y) => x.concat(y),
  }),
  context: Annotation<string>({
    reducer: (x, y) => y, // Reemplazar con el contexto más reciente
  }),
});

@Injectable()
export class AgentService {
  private app;
  private model = new ChatOpenAI({ modelName: 'gpt-4o', temperature: 0.7 });

  constructor(private ragService: RagService) {
    this.buildGraph();
  }

  private buildGraph() {
    const workflow = new StateGraph(AgentState)
      // NODO 1: Investigación (RAG)
      .addNode('research', async (state) => {
        const lastMessage = state.messages[state.messages.length - 1].content;
        // Recuperamos conocimiento del PDF
        const context = await this.ragService.retrieveContext(lastMessage);
        return { context };
      })
      // NODO 2: Generación de Estrategia y Markdown
      .addNode('generate_content', async (state) => {
        const query = state.messages[state.messages.length - 1].content;
        const context = state.context;
        
        // Auto-prompting implícito: Le damos un rol experto y contexto específico
        const prompt = `
          Eres un experto Senior en Marketing Digital y Productos Digitales.
          Usa el siguiente contexto recuperado de tus manuales: ${context}
          
          TAREA: ${query}
          
          FORMATO DE SALIDA:
          Debes responder SIEMPRE en formato Markdown (.md) válido.
          Incluye títulos, listas y tablas si es necesario.
          Si sugieres imágenes, descríbelas en detalle.
        `;
        
        const response = await this.model.invoke([new HumanMessage(prompt)]);
        return { messages: [response] };
      })
      // NODO 3: Generación de Imágenes (Opcional)
      .addNode('generate_image', async (state) => {
         // Lógica simplificada: si el último mensaje pide imagen, llamar a DALL-E
         // Aquí podrías usar una tool de LangChain [8]
         return {}; 
      })
      
      // Conexiones
      .addEdge(START, 'research')
      .addEdge('research', 'generate_content')
      .addEdge('generate_content', END); // Aquí podrías añadir lógica condicional para ir a 'generate_image'

    this.app = workflow.compile(); // [9]
  }

  async processRequest(userQuery: string) {
    const result = await this.app.invoke({
      messages: [new HumanMessage(userQuery)],
    });
    // Retornamos el último mensaje (la respuesta del bot)
    return result.messages[result.messages.length - 1].content;
  }
}
Paso 4: Capa de Voz (Entrada/Salida)
Para que sea "verbal", necesitas dos endpoints en tu controlador: uno que reciba el audio (blob) y otro que devuelva el audio generado.
Tecnología: Usaremos la API de OpenAI audio.transcriptions (Whisper) para escuchar y audio.speech (TTS) para hablar.
Archivo: src/app.controller.ts
import { Controller, Post, UploadedFile, UseInterceptors, Res } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { AgentService } from './agent/agent.service';
import OpenAI from 'openai';
import * as fs from 'fs';

@Controller('jarvis')
export class AppController {
  private openai = new OpenAI(); // Cliente oficial para métodos de audio

  constructor(private agentService: AgentService) {}

  @Post('talk')
  @UseInterceptors(FileInterceptor('audio'))
  async talkToJarvis(@UploadedFile() file: Express.Multer.File) {
    // 1. STT: Convertir voz a texto (Whisper)
    // Guardamos temporalmente el archivo para enviarlo a OpenAI
    const tempPath = `./uploads/${file.originalname}`;
    fs.writeFileSync(tempPath, file.buffer);
    
    const transcription = await this.openai.audio.transcriptions.create({
      file: fs.createReadStream(tempPath),
      model: 'whisper-1',
    });
    
    // 2. Cerebro: Procesar con RAG y LangGraph
    const textResponse = await this.agentService.processRequest(transcription.text);
    
    // 3. TTS: Convertir respuesta de texto a audio
    const mp3 = await this.openai.audio.speech.create({
      model: 'tts-1',
      voice: 'onyx', // Una voz tipo "Jarvis" grave
      input: textResponse.substring(0, 4096), // Límite de caracteres
    });
    
    const buffer = Buffer.from(await mp3.arrayBuffer());
    
    // Devolvemos: Texto (Markdown) + Audio (Base64 para reproducir en frontend)
    return {
      text_response: textResponse, // Aquí va tu contenido Markdown
      audio_base64: buffer.toString('base64')
    };
  }
}
Cómo funciona el flujo completo (Resumen)
1. Carga: Al inicio, el sistema carga tu PDF de marketing digital usando PDFLoader y lo indexa.
2. Escucha: Envías un audio: "Jarvis, basándote en el manual, crea un calendario de contenidos para Instagram sobre zapatos de cuero".
3. Transcribe: Whisper convierte el audio a texto.
4. Investiga (Auto-Prompting): LangGraph recibe el texto. El nodo research busca en el PDF estrategias sobre "Instagram" y "moda".
5. Genera: El nodo generate_content toma el contexto recuperado y escribe un archivo .md con la tabla de contenidos, hashtags y copy sugerido.
6. Habla: El sistema lee un resumen de la respuesta en voz alta y te entrega el archivo Markdown visual en tu frontend.
Tips Pro para Junior
• Prompt Engineering: En el paso 3, el secreto para el "auto-prompting" efectivo es pedirle al modelo que piense paso a paso antes de escribir el Markdown. Puedes añadir un nodo intermedio llamado plan_content que solo genere un esquema antes de escribir el post final.
• Imágenes: Para las imágenes de los posts, utiliza la herramienta DallEAPIWrapper de LangChain. Puedes pedirle al agente que, además del Markdown, devuelva un array de "prompts para imagen" y pasarlos automáticamente a DALL-E.
• Archivos .md: El LLM genera texto. Para guardarlo físicamente como archivo .md en el servidor, solo necesitas usar el módulo nativo fs de Node.js: fs.writeFileSync('estrategia.md', responseText).
Este esquema te da una base sólida, modular y escalable para tu sistema de marketing con IA. ¡A codear!