import {
  Box,
  Button,
  Container,
  Grid,
  Heading,
  Input,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useToast,
  Text,
} from "@chakra-ui/react";
import { useEffect, useRef } from "react";
import useDocumentStore from "../store/documentStore";

function Documents() {
  const {
    documents,
    isLoading,
    fetchDocuments,
    uploadDocuments,
    indexDocument,
  } = useDocumentStore();
  const fileInputRef = useRef();
  const toast = useToast();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    const response = await uploadDocuments(files);
    if (response) {
      toast({
        title: "Upload successful",
        description: response.message,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      fileInputRef.current.value = "";
    } else {
      toast({
        title: "Upload failed",
        description: "Please try again",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleReindex = async (docId) => {
    const response = await indexDocument(docId, true);
    if (response) {
      toast({
        title: "Reindex started",
        description: "Document will be reindexed shortly",
        status: "info",
        duration: 3000,
        isClosable: true,
      });
    } else {
      toast({
        title: "Reindex failed",
        description: "Please try again",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "pending":
        return "yellow";
      case "processing":
        return "blue";
      case "indexed":
        return "green";
      case "failed":
        return "red";
      default:
        return "gray";
    }
  };

  return (
    <Container maxW="container.xl" py={8}>
      <Grid gap={8}>
        <Box>
          <Heading size="lg" mb={4}>
            Documents
          </Heading>
          <Box
            p={6}
            borderWidth={2}
            borderRadius="lg"
            borderStyle="dashed"
            textAlign="center"
          >
            <Input
              type="file"
              multiple
              ref={fileInputRef}
              onChange={handleFileUpload}
              display="none"
            />
            <Button
              onClick={() => fileInputRef.current.click()}
              colorScheme="blue"
              isLoading={isLoading}
            >
              Upload Documents
            </Button>
            <Text mt={2} color="gray.600" fontSize="sm">
              Upload your documents to start chatting with them
            </Text>
          </Box>
        </Box>

        <Box overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Name</Th>
                <Th>Status</Th>
                <Th>Uploaded At</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {documents.map((doc) => (
                <Tr key={doc.id}>
                  <Td>{doc.title}</Td>
                  <Td>
                    <Badge colorScheme={getStatusColor(doc.status)}>
                      {doc.status}
                    </Badge>
                  </Td>
                  <Td>{new Date(doc.created_at).toLocaleString()}</Td>
                  <Td>
                    <Button
                      size="sm"
                      onClick={() => handleReindex(doc.id)}
                      isDisabled={doc.status === "processing"}
                    >
                      Reindex
                    </Button>
                  </Td>
                </Tr>
              ))}
              {documents.length === 0 && (
                <Tr>
                  <Td colSpan={4} textAlign="center" py={8}>
                    <Text color="gray.500">No documents uploaded yet</Text>
                  </Td>
                </Tr>
              )}
            </Tbody>
          </Table>
        </Box>
      </Grid>
    </Container>
  );
}

export default Documents;
