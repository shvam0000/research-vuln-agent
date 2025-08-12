import axios from "axios"
import dotenv from "dotenv"

dotenv.config()

const BASE_URL = process.env.LITELLM_BASE_URL!
const API_KEY = process.env.LITELLM_API_KEY!
const MODEL = "gpt-4.1"

export const callAgent = async (prompt: string): Promise<string> => {
  const response = await axios.post(
    `${BASE_URL}/chat/completions`,
    {
      model: MODEL,
      messages: [
        {
          role: "user",
          content:
            "Analyze a set of vulnerability data and provide a detailed report on potential security threats, including explanations of the identified vulnerabilities, their severity levels, and recommended mitigation strategies, as if you are a seasoned cybersecurity expert with extensive experience in threat analysis and vulnerability assessment.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
    },
    {
      headers: {
        Authorization: `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
    }
  )

  return response.data.choices[0].message.content || "No response from agent"
}
