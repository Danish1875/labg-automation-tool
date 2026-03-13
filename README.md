# AI-Powered Lab Guide Generation – Problem Statement
## Background Information

Cloud-based learning platforms often rely on **step-by-step lab guides** to help users perform tasks such as creating resources, configuring services, or testing applications. These guides are typically written in **Markdown format** so they can be easily rendered on web platforms or documentation systems.

Currently, creating these lab guides is a **manual and time-consuming process**. Authors must carefully write instructions, structure the document correctly, include commands or code blocks, and ensure that the guide follows a predefined template.

As the number of labs grows, maintaining consistency and producing new guides becomes increasingly difficult.

---

## The Core Problem

We need a way to **automatically generate structured lab guides** in Markdown format based on different types of inputs.

The inputs used to create a lab guide may vary. For example:

- A **Word document or PDF** that contains the instructions for a lab.
- A **prompt or description** explaining the goal of the lab.
- **Screenshots or images** that visually show steps performed in a system (for example, clicking buttons in a cloud portal).
- An **existing Markdown template** that defines the structure expected by the platform.

The challenge is that these inputs are often **unstructured** and may contain inconsistent formatting, incomplete instructions, or visual information that must be interpreted before it can be converted into a clear set of steps.

---

## Desired Outcome

The goal is to produce a **well-structured Markdown lab guide** that:

- Follows a predefined template or structure.
- Contains clear objectives and prerequisites.
- Includes step-by-step instructions.
- Uses properly formatted code blocks or commands where required.
- Is ready to be stored and version-controlled in a repository.

This Markdown file will ultimately serve as the **final lab guide that users interact with on the platform**.

---

## Challenges

Several challenges make this problem non-trivial:

- **Unstructured Inputs**  
  Instructions may come from different sources such as documents, screenshots, or prompts.

- **Understanding Visual Context**  
  Screenshots may contain important information about the sequence of actions performed.

- **Consistency of Lab Structure**  
  All guides must follow a consistent Markdown format even if the source material differs.

- **Code and Command Generation**  
  Some labs require commands or scripts that users must execute in a sandbox or terminal environment.

- **Scalability**  
  As the number of labs increases, the system should be able to process many lab generation tasks efficiently.

---

## Purpose of This Repository

This repository serves as a **foundation for contributors to explore and address this problem**. The goal is to experiment with approaches that can transform different forms of input into consistent and usable lab documentation.

Contributors should focus on understanding the problem space, the constraints involved, and the types of inputs that may be used to generate lab guides.

This document is intended to provide a **clear reference point for the problem we are trying to solve**, without prescribing a specific implementation or solution.
