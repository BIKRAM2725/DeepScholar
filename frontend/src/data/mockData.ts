export interface Paper {
  title: string;
  authors: string;
  year: number;
  abstract: string;
  link: string;
}

export interface SearchResult {
  query: string;
  summary: string;
  key_points: string[];
  papers: Paper[];
}

export const mockResults: Record<string, SearchResult> = {
  "quantum computing": {
    query: "Quantum Computing",
    summary:
      "Quantum computing leverages the principles of quantum mechanics—superposition, entanglement, and interference—to process information in fundamentally new ways. Unlike classical computers that operate on binary bits, quantum computers use qubits that can exist in multiple states simultaneously, enabling them to solve certain classes of problems exponentially faster. Recent breakthroughs in error correction and hardware stability have brought practical quantum advantage closer to reality, with implications spanning cryptography, drug discovery, materials science, and optimization.",
    key_points: [
      "Qubits exploit superposition and entanglement to represent and process exponentially more information than classical bits.",
      "Quantum error correction remains a central challenge; surface codes and topological approaches show the most promise.",
      "Near-term 'noisy intermediate-scale quantum' (NISQ) devices are already demonstrating advantage on specific sampling tasks.",
      "Post-quantum cryptography standards are being adopted preemptively to protect against future quantum attacks on RSA and ECC.",
      "Hybrid quantum-classical algorithms like VQE and QAOA bridge current hardware limitations with practical use cases.",
    ],
    papers: [
      {
        title: "Quantum Supremacy Using a Programmable Superconducting Processor",
        authors: "F. Arute, K. Arya, R. Babbush et al. (Google AI Quantum)",
        year: 2019,
        abstract:
          "We report the use of a 53-qubit processor to perform a computational task in 200 seconds that would take a state-of-the-art classical supercomputer approximately 10,000 years, establishing quantum computational supremacy for the first time.",
        link: "https://www.nature.com/articles/s41586-019-1666-5",
      },
      {
        title: "Quantum Error Correction Beyond Break-Even",
        authors: "V. V. Sivak, A. Eickbusch, B. Royer et al.",
        year: 2023,
        abstract:
          "We demonstrate a quantum error-correcting code that surpasses the break-even point, where the logical qubit lifetime exceeds that of any of the individual physical components, using a bosonic code in a superconducting circuit.",
        link: "https://www.nature.com/articles/s41586-022-05434-1",
      },
      {
        title: "Quantum Approximate Optimization Algorithm: Performance, Mechanism, and Implementation",
        authors: "L. Zhou, S.-T. Wang, S. Choi et al.",
        year: 2020,
        abstract:
          "We study the performance of the Quantum Approximate Optimization Algorithm on MaxCut problems, analyzing the interplay between circuit depth, problem structure, and solution quality across various graph types.",
        link: "https://journals.aps.org/prx/abstract/10.1103/PhysRevX.10.021067",
      },
      {
        title: "Suppressing Quantum Errors by Scaling a Surface Code Logical Qubit",
        authors: "Google Quantum AI",
        year: 2023,
        abstract:
          "We show that increasing the size of a surface code from distance-3 to distance-5 reduces logical error rates, demonstrating that quantum error correction can be scaled to suppress errors in practice.",
        link: "https://www.nature.com/articles/s41586-022-05434-1",
      },
      {
        title: "Variational Quantum Eigensolver for Electronic Structure Calculations",
        authors: "A. Peruzzo, J. McClean, P. Shadbolt et al.",
        year: 2014,
        abstract:
          "We propose and experimentally implement a variational quantum eigensolver, a quantum-classical hybrid algorithm for finding the ground-state energy of molecules, demonstrating its feasibility on photonic quantum hardware.",
        link: "https://www.nature.com/articles/ncomms5213",
      },
    ],
  },
  "machine learning": {
    query: "Machine Learning",
    summary:
      "Machine learning is a subset of artificial intelligence focused on developing algorithms that improve automatically through experience. Modern deep learning architectures, particularly transformers and large language models, have revolutionized natural language processing, computer vision, and generative AI. The field is rapidly evolving with advances in self-supervised learning, reinforcement learning from human feedback, and multimodal models that can process text, images, and audio simultaneously.",
    key_points: [
      "Transformer architectures have become the dominant paradigm, powering breakthroughs from GPT to vision transformers.",
      "Self-supervised and contrastive learning methods reduce dependence on labeled data at scale.",
      "Reinforcement learning from human feedback (RLHF) has proven critical for aligning large language models.",
      "Scaling laws suggest predictable performance gains with increased model size, data, and compute.",
      "Interpretability and safety research is gaining urgency as models become more capable and widely deployed.",
    ],
    papers: [
      {
        title: "Attention Is All You Need",
        authors: "A. Vaswani, N. Shazeer, N. Parmar et al.",
        year: 2017,
        abstract:
          "We propose the Transformer, a novel architecture based entirely on attention mechanisms, dispensing with recurrence and convolutions. It achieves state-of-the-art results on machine translation while being more parallelizable and faster to train.",
        link: "https://arxiv.org/abs/1706.03762",
      },
      {
        title: "Language Models are Few-Shot Learners",
        authors: "T. Brown, B. Mann, N. Ryder et al. (OpenAI)",
        year: 2020,
        abstract:
          "We demonstrate that scaling language models to 175 billion parameters (GPT-3) results in strong few-shot performance on many NLP tasks without task-specific fine-tuning, approaching competitive results with state-of-the-art fine-tuned systems.",
        link: "https://arxiv.org/abs/2005.14165",
      },
      {
        title: "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
        authors: "A. Dosovitskiy, L. Beyer, A. Kolesnikov et al.",
        year: 2021,
        abstract:
          "We show that a pure transformer applied directly to sequences of image patches can perform very well on image classification tasks, challenging the dominance of convolutional neural networks.",
        link: "https://arxiv.org/abs/2010.11929",
      },
      {
        title: "Training Language Models to Follow Instructions with Human Feedback",
        authors: "L. Ouyang, J. Wu, X. Jiang et al. (OpenAI)",
        year: 2022,
        abstract:
          "We demonstrate that fine-tuning language models with reinforcement learning from human feedback (RLHF) significantly improves their ability to follow user intent and reduces harmful outputs.",
        link: "https://arxiv.org/abs/2203.02155",
      },
      {
        title: "Deep Residual Learning for Image Recognition",
        authors: "K. He, X. Zhang, S. Ren, J. Sun",
        year: 2016,
        abstract:
          "We present a residual learning framework to ease the training of very deep networks. These residual networks are substantially deeper than those used previously, achieving state-of-the-art results on ImageNet.",
        link: "https://arxiv.org/abs/1512.03385",
      },
    ],
  },
};

export const recentSearches = [
  "Quantum Computing",
  "Machine Learning",
  "Blockchain Consensus",
  "CRISPR Gene Editing",
  "Neural Architecture Search",
];

export function getSearchResult(query: string): SearchResult {
  const key = query.toLowerCase().trim();
  if (mockResults[key]) return mockResults[key];

  // Default fallback
  return {
    ...mockResults["quantum computing"],
    query,
  };
}
