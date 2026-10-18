import Pyjoyment.Plugin


class Pyjoyment_Plugin_MyRenderer(Pyjoyment.Plugin.object):
    def register(self, app, conf):

        # Add "mine" handler
        def mine(renderer, c, output, options):

            # Check for one-time use inline template
            inline_template = options.get('inline')

            # Check for appropriate template in "templates" directories
            template_path = renderer.template_path(options)

            # Check for appropriate template in DATA sections
            data_template = renderer.get_data_template(options)

            # This part is up to you and your template system :)
            template = inline_template or data_template
            if template is None and template_path is not None:
                with open(template_path, encoding='utf-8') as file:
                    template = file.read()

            # Or just raise an exception if an error occurs
            if template is None:
                raise Exception('Something went wrong with the template')

            # Pass the rendered result back to the renderer
            output.write(template.replace('World', 'Pyjoyment'))

        app.renderer.add_handler('mine', mine)


object = Pyjoyment_Plugin_MyRenderer
