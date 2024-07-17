# trial_llama-prototype
This repository contains proof-of-concept code in Jupyter notebook form, demonstrating how we are using AI for cancer clinical trial matching at Dana-Farber Cancer Institute. It is not usable directly by external parties, since the embedding similarity model used to filter for a small set of trials to consider is not released yet. The purpose of the code and notebooks is to provide a conceptual overview of how we are addressing this problem technically.

**Feel free to reach out with questions, thoughts, collaborations!**

## Motivation
Developing new cancer therapies relies on performing clinical trials to test treatments. Unfortunately, up to 20% of trials fail due to insufficient patient participation, and only 7% of adults with cancer join these trials. Quickly matching patients to suitable trials is crucial but challenging due to the complexity of modern trials, which often have strict eligibility criteria.

Previously, Dana-Farber created [MatchMiner](matchminer.org), an open-source tool that matches patients to trials based on their tumor's genetic mutations. To enhance this process, we aim to use Llama-3 and other AI methods to extract crucial data from unstructured text in electronic health records, such as cancer subtype, treatment history, and treatment goals, and incorporate it into MatchMiner. This improvement will help match patients to trials more effectively and lay the groundwork for expanding MatchMiner to other cancer centers, ultimately accelerating cancer treatment development and improving patient outcomes.

## Notebooks
The notebook folder contains code that provides an overview of how we used various technologies, especially Llama-3, to construct a prototype. The notebooks themselves are not directly executable by external parties, as they require access to models and information that has not yet been released. However, in the future, these notebooks will become more stand-alone, referencing public information only.

## App code
We have constructed a prototype highlighting how these technologies can be used to create a functional trial matching system. The app is still depenent on external APIs (Groq for trial checking) and private APIs for trial similarity and therefore is not reproducible by external users. However the code is available for reference, it is built using the rapid prototyping application framework from Holoviz called Panel.

**Use github to start a conversation!**


