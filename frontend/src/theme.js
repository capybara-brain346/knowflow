import { extendTheme } from '@chakra-ui/react';

const config = {
    initialColorMode: 'light',
    useSystemColorMode: true,
};

const theme = extendTheme({
    config,
    fonts: {
        heading: 'Inter, system-ui, sans-serif',
        body: 'Inter, system-ui, sans-serif',
    },
    styles: {
        global: (props) => ({
            body: {
                bg: props.colorMode === 'light' ? 'white' : 'gray.800',
            },
        }),
    },
    components: {
        Button: {
            defaultProps: {
                variant: 'solid',
            },
        },
    },
});

export default theme; 