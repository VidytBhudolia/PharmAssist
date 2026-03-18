import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Loader2,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  FileText,
  Maximize2,
  Minimize2,
} from "lucide-react";
import * as pdfjsLib from "pdfjs-dist";

// Configure PDF.js worker - use CDN for reliability
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

/**
 * PDFViewerModal v2 - Custom PDF viewer using PDF.js
 *
 * Features:
 * - Consistent rendering across all browsers (Brave, Safari, Chrome, etc.)
 * - No browser PDF controls (download, print buttons hidden)
 * - Custom zoom controls
 * - Page navigation
 * - Right-click disabled (prototype protection)
 * - Clean, professional UI
 */
export function PDFViewerModal({
  isOpen,
  onClose,
  pdfUrl,
  title = "Report Viewer",
  isLoading = false,
  error = null,
}) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [pdfDoc, setPdfDoc] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [baseScale, setBaseScale] = useState(1.0); // Fit-to-width scale (internal)
  const [zoomLevel, setZoomLevel] = useState(1.0); // User-facing zoom: 1.0 = 100%
  const [rendering, setRendering] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const [renderedPages, setRenderedPages] = useState([]);

  // The actual rendering scale = baseScale * zoomLevel
  const scale = baseScale * zoomLevel;

  const containerRef = useRef(null);
  const canvasRefs = useRef({});

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  // Load PDF document
  useEffect(() => {
    if (!pdfUrl || !isOpen) return;

    console.log("[PDFViewerModal v2] Loading PDF from URL:", pdfUrl);
    setLoadError(null);
    setRendering(true);

    const loadPDF = async () => {
      try {
        const loadingTask = pdfjsLib.getDocument(pdfUrl);
        const pdf = await loadingTask.promise;

        console.log("[PDFViewerModal v2] PDF loaded successfully, pages:", pdf.numPages);
        setPdfDoc(pdf);
        setTotalPages(pdf.numPages);
        setCurrentPage(1);
        setRendering(false);
      } catch (err) {
        console.error("[PDFViewerModal v2] Error loading PDF:", err);
        setLoadError(err.message || "Failed to load PDF");
        setRendering(false);
      }
    };

    loadPDF();

    return () => {
      if (pdfDoc) {
        pdfDoc.destroy();
      }
    };
  }, [pdfUrl, isOpen]);

  // Render current page
  useEffect(() => {
    if (!pdfDoc) return;

    const renderAllPages = async () => {
      setRendering(true);
      try {
        const pages = [];
        for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
          pages.push(pageNum);
        }
        setRenderedPages(pages);
        setRendering(false);
      } catch (err) {
        console.error("[PDFViewerModal v2] Error preparing pages:", err);
        setRendering(false);
      }
    };

    renderAllPages();
  }, [pdfDoc]);

  // Render individual page on canvas
  useEffect(() => {
    if (!pdfDoc || renderedPages.length === 0) return;

    const renderPage = async (pageNum) => {
      const canvas = canvasRefs.current[pageNum];
      if (!canvas) return;

      try {
        const page = await pdfDoc.getPage(pageNum);
        const context = canvas.getContext("2d");

        // Get device pixel ratio for crisp rendering on retina displays
        const devicePixelRatio = window.devicePixelRatio || 1;

        // Get original viewport at scale
        const viewport = page.getViewport({ scale: scale * devicePixelRatio });

        // Set canvas internal size (scaled by device pixel ratio)
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        // Set canvas display size (CSS pixels)
        canvas.style.width = `${viewport.width / devicePixelRatio}px`;
        canvas.style.height = `${viewport.height / devicePixelRatio}px`;

        // Render PDF page at higher resolution
        const renderContext = {
          canvasContext: context,
          viewport: viewport,
        };

        await page.render(renderContext).promise;
        console.log(
          `[PDFViewerModal v2] Rendered page ${pageNum}, DPR: ${devicePixelRatio}, dimensions: ${viewport.width}x${viewport.height}`,
        );
      } catch (err) {
        console.error(`[PDFViewerModal v2] Error rendering page ${pageNum}:`, err);
      }
    };

    // Render all pages
    renderedPages.forEach((pageNum) => renderPage(pageNum));
  }, [pdfDoc, renderedPages, scale]);

  // Auto-adjust base scale to fit container width
  useEffect(() => {
    if (!pdfDoc || !containerRef.current) return;

    const adjustScale = async () => {
      const page = await pdfDoc.getPage(1);
      const viewport = page.getViewport({ scale: 1 });
      const container = containerRef.current;

      // Calculate scale to fit width (with padding)
      const containerWidth = container.clientWidth - 80; // 40px padding each side
      const scaleToFit = containerWidth / viewport.width;

      console.log(
        `[PDFViewerModal v2] Auto-scale: container=${containerWidth}px, page=${viewport.width}px, baseScale=${scaleToFit}`,
      );
      setBaseScale(scaleToFit);
    };

    adjustScale();
  }, [pdfDoc, isFullscreen]);

  // Track current page based on scroll position
  useEffect(() => {
    if (!containerRef.current || totalPages === 0) return;

    const handleScroll = () => {
      const container = containerRef.current;
      if (!container) return;

      // Find which page is most visible
      const canvases = Object.values(canvasRefs.current).filter(Boolean);
      let maxVisibility = 0;
      let mostVisiblePage = 1;

      canvases.forEach((canvas, index) => {
        const rect = canvas.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();

        // Calculate how much of the canvas is visible
        const visibleTop = Math.max(rect.top, containerRect.top);
        const visibleBottom = Math.min(rect.bottom, containerRect.bottom);
        const visibleHeight = Math.max(0, visibleBottom - visibleTop);
        const visibility = visibleHeight / rect.height;

        if (visibility > maxVisibility) {
          maxVisibility = visibility;
          mostVisiblePage = index + 1;
        }
      });

      setCurrentPage(mostVisiblePage);
    };

    const container = containerRef.current;
    container.addEventListener("scroll", handleScroll);

    return () => {
      container.removeEventListener("scroll", handleScroll);
    };
  }, [totalPages]);

  // Disable right-click
  const handleContextMenu = useCallback((e) => {
    e.preventDefault();
    return false;
  }, []);

  // Navigation handlers - scroll to specific page
  const goToNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      const nextCanvas = canvasRefs.current[currentPage + 1];
      if (nextCanvas) {
        nextCanvas.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [currentPage, totalPages]);

  const goToPreviousPage = useCallback(() => {
    if (currentPage > 1) {
      const prevCanvas = canvasRefs.current[currentPage - 1];
      if (prevCanvas) {
        prevCanvas.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [currentPage]);

  // Zoom handlers — adjust zoomLevel relative to fit-to-width baseline
  const zoomIn = useCallback(() => {
    setZoomLevel((prev) => Math.min(prev + 0.1, 3.0));
  }, []);

  const zoomOut = useCallback(() => {
    setZoomLevel((prev) => Math.max(prev - 0.1, 0.3));
  }, []);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[200]"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-0 flex items-center justify-center z-[201] p-4 pointer-events-none"
          >
            <div
              className={`bg-card border border-border/70 rounded-2xl shadow-2xl flex flex-col pointer-events-auto transition-all duration-300 ${
                isFullscreen ? "w-full h-full rounded-none" : "w-[95vw] max-w-6xl h-[90vh]"
              }`}
              onClick={(e) => e.stopPropagation()}
              onContextMenu={handleContextMenu}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-border/60 bg-muted/30 rounded-t-2xl flex-shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/15 border border-primary/30 flex items-center justify-center">
                    <FileText size={18} className="text-primary" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-foreground">{title}</h2>
                    <p className="text-xs text-muted-foreground">
                      {totalPages > 0
                        ? `Viewing page ${currentPage} of ${totalPages} • Scroll to navigate`
                        : "Loading..."}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Page Navigation */}
                  {totalPages > 1 && (
                    <>
                      <button
                        onClick={goToPreviousPage}
                        disabled={currentPage === 1}
                        className="p-2 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Previous page"
                      >
                        <ChevronLeft size={18} />
                      </button>
                      <button
                        onClick={goToNextPage}
                        disabled={currentPage === totalPages}
                        className="p-2 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Next page"
                      >
                        <ChevronRight size={18} />
                      </button>
                      <div className="w-px h-6 bg-border mx-1" />
                    </>
                  )}

                  {/* Zoom Controls */}
                  <button
                    onClick={zoomOut}
                    disabled={zoomLevel <= 0.3}
                    className="p-2 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Zoom out"
                  >
                    <ZoomOut size={18} />
                  </button>
                  <span className="text-xs text-muted-foreground font-medium min-w-[3rem] text-center">
                    {Math.round(zoomLevel * 100)}%
                  </span>
                  <button
                    onClick={zoomIn}
                    disabled={zoomLevel >= 3.0}
                    className="p-2 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Zoom in"
                  >
                    <ZoomIn size={18} />
                  </button>

                  <div className="w-px h-6 bg-border mx-1" />

                  {/* Fullscreen Toggle */}
                  <button
                    onClick={toggleFullscreen}
                    className="p-2 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors"
                    title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
                  >
                    {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                  </button>

                  {/* Close Button */}
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-destructive/10 rounded-lg text-muted-foreground hover:text-destructive transition-colors"
                    title="Close (ESC)"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>

              {/* Content Area */}
              <div ref={containerRef} className="flex-1 relative overflow-auto bg-muted/20">
                {/* Loading State */}
                {(isLoading || rendering) && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm z-10">
                    <div className="flex flex-col items-center gap-4 p-8 rounded-2xl bg-card border border-border/50 shadow-lg">
                      <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                        <Loader2 className="animate-spin text-primary" size={32} />
                      </div>
                      <div className="text-center">
                        <p className="text-foreground font-medium">
                          {isLoading ? "Generating Report..." : "Rendering Page..."}
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {isLoading
                            ? "This may take a few moments"
                            : `Page ${currentPage} of ${totalPages}`}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error State */}
                {(error || loadError) && !isLoading && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm z-10">
                    <div className="flex flex-col items-center gap-4 p-8 rounded-2xl bg-card border border-destructive/30 shadow-lg max-w-md">
                      <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
                        <AlertCircle className="text-destructive" size={32} />
                      </div>
                      <div className="text-center">
                        <p className="text-foreground font-medium">Failed to Load Report</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {error || loadError || "Unable to display the PDF."}
                        </p>
                      </div>
                      <button
                        onClick={onClose}
                        className="px-4 py-2 bg-muted hover:bg-muted/80 text-foreground rounded-lg text-sm font-medium transition-colors"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                )}

                {/* PDF Canvas - Custom rendering with PDF.js - All pages scrollable */}
                {pdfDoc && !error && !loadError && (
                  <div className="flex flex-col items-center gap-6 py-6 px-4 min-h-full bg-muted/20">
                    {renderedPages.map((pageNum) => (
                      <div
                        key={pageNum}
                        className="bg-white shadow-2xl relative"
                        style={{
                          maxWidth: "100%",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                        }}
                      >
                        {/* Page number indicator */}
                        <div className="absolute top-4 right-4 bg-black/70 text-white px-3 py-1.5 rounded-full text-xs font-medium z-10 shadow-lg">
                          Page {pageNum} of {totalPages}
                        </div>
                        <canvas
                          ref={(el) => {
                            if (el) canvasRefs.current[pageNum] = el;
                          }}
                          className="block"
                          style={{
                            maxWidth: "100%",
                            height: "auto",
                          }}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-5 py-3 border-t border-border/60 bg-muted/30 rounded-b-2xl flex-shrink-0">
                <p className="text-xs text-muted-foreground">
                  📄 Confidential Report • For authorized viewing only
                </p>
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg text-sm font-medium transition-colors shadow-sm"
                >
                  Close Viewer
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default PDFViewerModal;
