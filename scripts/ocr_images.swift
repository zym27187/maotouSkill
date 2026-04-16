#!/usr/bin/env swift

import Foundation
import Vision

struct OCRLine {
    let text: String
    let minX: CGFloat
    let minY: CGFloat
    let maxY: CGFloat
}

func recognizeText(in path: String) throws -> [OCRLine] {
    let url = URL(fileURLWithPath: path)

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    request.minimumTextHeight = 0.015

    let handler = try VNImageRequestHandler(url: url, options: [:])
    try handler.perform([request])

    guard let observations = request.results else {
        return []
    }

    return observations.compactMap { observation in
        guard let candidate = observation.topCandidates(1).first else {
            return nil
        }
        let text = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            return nil
        }
        return OCRLine(
            text: text,
            minX: observation.boundingBox.minX,
            minY: observation.boundingBox.minY,
            maxY: observation.boundingBox.maxY
        )
    }
}

func sortLines(_ lines: [OCRLine]) -> [OCRLine] {
    return lines.sorted { lhs, rhs in
        let rowDelta = abs(lhs.maxY - rhs.maxY)
        if rowDelta > 0.03 {
            return lhs.maxY > rhs.maxY
        }
        return lhs.minX < rhs.minX
    }
}

let args = Array(CommandLine.arguments.dropFirst())

if args.isEmpty {
    FileHandle.standardError.write(Data("usage: ocr_images.swift <image> [image...]\n".utf8))
    exit(1)
}

for path in args {
    print("=== \(path) ===")
    do {
        let lines = try sortLines(recognizeText(in: path))
        if lines.isEmpty {
            print("[NO_TEXT]")
        } else {
            for line in lines {
                print(line.text)
            }
        }
    } catch {
        print("[ERROR] \(error.localizedDescription)")
    }
    print("")
}
