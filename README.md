# trial_llama-prototype
This is a proof of concept code / notebook demonstrating how to use AI for clinical trial matching. It is not usable directly as the similarity model used to find a small set of trials to consider is not released yet. The purpose of the code and nodebooks is to give a conceptual overview of how we are addressing this problem technically.

**Feel free to reach out with questions, thoughts, collaborations!**

## Motivation
Developing new cancer therapies relies on clinical trials to test treatments. Unfortunately, up to 20% of trials fail due to insufficient patient participation, and only 7% of adults with cancer join these trials. Quickly matching patients to suitable trials is crucial but challenging due to the complexity of modern trials, which often have strict eligibility criteria.

Previously Dana-Farber created [MatchMiner](matchminer.org), an open-source tool that matches patients to trials based on their tumor's genetic mutations. To enhance this process, we aim to use Llama-3 and other AI to extract crucial data from unstructured text in electronic health records, such as cancer subtype, treatment history, and treatment goals, and incorporate it into MatchMiner. This improvement will help match patients to trials more effectively and lay the groundwork for expanding MatchMiner to other cancer centers, ultimately accelerating cancer treatment development and improving patient outcomes.

## Notebooks
The notebook folder contains a series of codes which provide an overview of how we used various technologies, most especially Llama to construct a prototype. The notebooks themselves are not directly runnable by external as the request information that has not yet been released. However in the future these notebooks will become more stand-alone referencing only public information.

## App code
We have constructed a prototype highlighting how these technologies can be used to create a functional trial matching system. The app is still depenent on external APIs (Groq for trial checking) and private APIs for trial similarity and therefore is not reproducible by external users. However the code is available for reference, it is built using the rapid prototyping application framework from Holoviz called Panel.

**Use github to start a conversation!**


