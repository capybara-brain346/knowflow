import {
  Box,
  Button,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverHeader,
  Checkbox,
  VStack,
  HStack,
  Text,
  Badge,
} from "@chakra-ui/react";
import { useState, useEffect } from "react";
import useDocumentStore from "../store/documentStore";

function DocumentSelector({ selectedDocs, onSelectionChange }) {
  const { documents, fetchDocuments } = useDocumentStore();
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleToggleDocument = (docId) => {
    const newSelection = selectedDocs.includes(docId)
      ? selectedDocs.filter((id) => id !== docId)
      : [...selectedDocs, docId];
    onSelectionChange(newSelection);
  };

  return (
    <Popover
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
      placement="top-start"
    >
      <PopoverTrigger>
        <Button
          size="sm"
          onClick={() => setIsOpen(!isOpen)}
          variant="outline"
          colorScheme={selectedDocs.length > 0 ? "blue" : "gray"}
        >
          {selectedDocs.length > 0
            ? `${selectedDocs.length} Documents Selected`
            : "Select Documents"}
        </Button>
      </PopoverTrigger>
      <PopoverContent>
        <PopoverHeader fontWeight="semibold">
          Select Documents to Query
        </PopoverHeader>
        <PopoverBody maxH="300px" overflowY="auto">
          <VStack align="stretch" spacing={2}>
            {documents
              .filter((doc) => doc.status === "indexed")
              .map((doc) => (
                <HStack key={doc.doc_id} justify="space-between">
                  <Checkbox
                    isChecked={selectedDocs.includes(doc.doc_id)}
                    onChange={() => handleToggleDocument(doc.doc_id)}
                  >
                    <Text fontSize="sm" noOfLines={1}>
                      {doc.title}
                    </Text>
                  </Checkbox>
                  <Badge colorScheme="green" fontSize="xs">
                    indexed
                  </Badge>
                </HStack>
              ))}
            {documents.filter((doc) => doc.status === "indexed").length ===
              0 && (
              <Text color="gray.500" fontSize="sm">
                No indexed documents available
              </Text>
            )}
          </VStack>
        </PopoverBody>
      </PopoverContent>
    </Popover>
  );
}

export default DocumentSelector;
