import {
  Box,
  Button,
  Container,
  Flex,
  Grid,
  GridItem,
  Input,
  Text,
  VStack,
  useToast,
  IconButton,
  HStack,
} from "@chakra-ui/react";
import { useEffect, useRef, useState } from "react";
import useChatStore from "../store/chatStore";
import { EditIcon, CheckIcon, CloseIcon } from "@chakra-ui/icons";

function Chat() {
  const {
    sessions,
    currentSession,
    fetchSessions,
    createSession,
    setCurrentSession,
    sendMessage,
    deleteSession,
    renameSession,
  } = useChatStore();
  const messageInputRef = useRef();
  const chatContainerRef = useRef();
  const toast = useToast();
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [currentSession?.messages]);

  const handleNewSession = async () => {
    const title = `Chat ${sessions.length + 1}`;
    await createSession(title);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const message = messageInputRef.current.value.trim();
    if (!message) return;

    if (!currentSession) {
      const session = await createSession("New Chat");
      if (!session) return;
    }

    messageInputRef.current.value = "";
    const response = await sendMessage(message, currentSession.id);

    if (!response) {
      toast({
        title: "Failed to send message",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleDeleteSession = async (sessionId) => {
    await deleteSession(sessionId);
  };

  const handleStartRename = (session) => {
    setEditingSessionId(session.id);
    setNewTitle(session.title);
  };

  const handleCancelRename = () => {
    setEditingSessionId(null);
    setNewTitle("");
  };

  const handleRename = async (sessionId) => {
    if (!newTitle.trim()) {
      return;
    }

    const success = await renameSession(sessionId, newTitle.trim());
    if (success) {
      setEditingSessionId(null);
      setNewTitle("");
    } else {
      toast({
        title: "Failed to rename chat",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  return (
    <Container maxW="container.xl" h="calc(100vh - 80px)">
      <Grid templateColumns="250px 1fr" h="100%" gap={4}>
        <GridItem borderRight="1px" borderColor="gray.200" overflowY="auto">
          <VStack spacing={4} align="stretch" p={4}>
            <Button colorScheme="blue" onClick={handleNewSession}>
              New Chat
            </Button>
            {sessions.map((session) => (
              <Box
                key={session.id}
                p={3}
                bg={currentSession?.id === session.id ? "blue.50" : "transparent"}
                borderRadius="md"
                cursor="pointer"
                onClick={() => setCurrentSession(session)}
                position="relative"
              >
                {editingSessionId === session.id ? (
                  <HStack>
                    <Input
                      size="sm"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      autoFocus
                    />
                    <IconButton
                      size="sm"
                      icon={<CheckIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRename(session.id);
                      }}
                    />
                    <IconButton
                      size="sm"
                      icon={<CloseIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancelRename();
                      }}
                    />
                  </HStack>
                ) : (
                  <HStack justify="space-between" width="100%">
                    <Text noOfLines={1}>{session.title}</Text>
                    <HStack spacing={1}>
                      <IconButton
                        size="xs"
                        icon={<EditIcon />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartRename(session);
                        }}
                      />
                      <Button
                        size="xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSession(session.id);
                        }}
                      >
                        Delete
                      </Button>
                    </HStack>
                  </HStack>
                )}
              </Box>
            ))}
          </VStack>
        </GridItem>

        <GridItem display="flex" flexDirection="column">
          <Box flex={1} overflowY="auto" p={4} ref={chatContainerRef}>
            {currentSession?.messages?.map((message, index) => (
              <Box
                key={index}
                mb={4}
                p={4}
                borderRadius="lg"
                bg={message.sender === "user" ? "blue.50" : "gray.50"}
                alignSelf={
                  message.sender === "user" ? "flex-end" : "flex-start"
                }
                maxW="80%"
              >
                <Text>{message.content}</Text>
              </Box>
            ))}
          </Box>

          <Box p={4} borderTop="1px" borderColor="gray.200">
            <form onSubmit={handleSendMessage}>
              <Flex gap={2}>
                <Input
                  ref={messageInputRef}
                  placeholder="Type your message..."
                  disabled={!currentSession}
                />
                <Button
                  type="submit"
                  colorScheme="blue"
                  disabled={!currentSession}
                >
                  Send
                </Button>
              </Flex>
            </form>
          </Box>
        </GridItem>
      </Grid>
    </Container>
  );
}

export default Chat;
