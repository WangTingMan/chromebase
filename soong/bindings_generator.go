package libchrome

import (
	"fmt"
	"path"
	"strings"

	"android/soong/android"
	"android/soong/genrule"

	"github.com/google/blueprint"
)

func init() {
	android.RegisterModuleType("generate_mojom_downgraded_files", mojomDowngradedFilesFactory)
	android.RegisterModuleType("generate_mojom_pickles", mojomPicklesFactory)
	android.RegisterModuleType("generate_mojom_headers", mojomHeadersFactory)
	android.RegisterModuleType("generate_mojom_srcs", mojomSrcsFactory)
	android.RegisterModuleType("generate_mojom_srcjar", mojomSrcjarFactory)
}

var (
	pctx = android.NewPackageContext("android/soong/external/libchrome")

	mojomBindingsGenerator = pctx.HostBinToolVariable("mojomBindingsGenerator", "mojom_bindings_generator")
	mojomTypesDowngrader   = pctx.HostBinToolVariable("mojomTypesDowngrader", "mojom_types_downgrader")
	mergeZips              = pctx.HostBinToolVariable("mergeZips", "merge_zips")

	downgradeMojomTypesRule = pctx.StaticRule("downgradeMojomTypesRule", blueprint.RuleParams{
		Command: `${mojomTypesDowngrader}
		${in}
		--outdir ${outDir}`,
		CommandDeps: []string{
			"${mojomTypesDowngrader}",
		},
		Description: "Downgrade mojom files $in => $out",
	}, "outDir")

	generateMojomPicklesRule = pctx.StaticRule("generateMojomPicklesRule", blueprint.RuleParams{
		Command: `${mojomBindingsGenerator}
		--use_bundled_pylibs parse
		-d ${package}
		${flags}
		-o ${outDir}
		${in}`,
		CommandDeps: []string{
			"${mojomBindingsGenerator}",
		},
		Description: "Mojo pickles generation $in => $out",
		Restat:      true,
	}, "package", "flags", "outDir")

	generateMojomSrcsRule = pctx.StaticRule("generateMojomSrcsRule", blueprint.RuleParams{
		Command: `${mojomBindingsGenerator}
		--use_bundled_pylibs generate
		-o ${outDir}
		-I=${package}:${package}
		-d ${package}
		${flags}
		--bytecode_path=${templateDir}
		--generators=${mojomGenerator}
		--use_new_wrapper_types
		${in}`,
		CommandDeps: []string{
			"${mojomBindingsGenerator}",
		},
		Description: "Mojo sources generation $in => $out",
		Restat:      true,
	}, "mojomGenerator", "package", "flags", "outDir", "templateDir")

	mergeSrcjarsRule = pctx.StaticRule("mergeSrcjarsRule", blueprint.RuleParams{
		Command: "${mergeZips} ${out} ${in}",
		CommandDeps: []string{
			"${mergeZips}",
		},
		Description: "Merge .srcjars $in => $out",
	})
)

type mojomDowngradedFilesProperties struct {
	// list of input files
	Srcs []string
}

type mojomDowngradedFiles struct {
	android.ModuleBase

	properties mojomDowngradedFilesProperties

	generatedSrcs android.Paths
	outDir        android.Path
}

var _ genrule.SourceFileGenerator = (*mojomDowngradedFiles)(nil)

func (m *mojomDowngradedFiles) DepsMutator(ctx android.BottomUpMutatorContext) {
	android.ExtractSourcesDeps(ctx, m.properties.Srcs)
}

func (m *mojomDowngradedFiles) GenerateAndroidBuildActions(ctx android.ModuleContext) {
	m.outDir = android.PathForModuleGen(ctx, "")

	for _, in := range ctx.ExpandSources(m.properties.Srcs, nil) {
		if !strings.HasSuffix(in.Rel(), ".mojom") {
			ctx.PropertyErrorf("srcs", "Source is not a .mojom file: %s", in.Rel())
			continue
		}

		out := android.PathForModuleGen(ctx, in.Rel())
		m.generatedSrcs = append(m.generatedSrcs, out)

		ctx.ModuleBuild(pctx, android.ModuleBuildParams{
			Rule:   downgradeMojomTypesRule,
			Input:  in,
			Output: out,
			Args: map[string]string{
				"outDir":  path.Dir(out.String()),
			},
		})
	}
}

func (m *mojomDowngradedFiles) GeneratedHeaderDirs() android.Paths {
	return nil
}

func (m *mojomDowngradedFiles) GeneratedDeps() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomDowngradedFiles) GeneratedSourceFiles() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomDowngradedFiles) Srcs() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func mojomDowngradedFilesFactory() android.Module {
	m := &mojomDowngradedFiles{}
	m.AddProperties(&m.properties)
	android.InitAndroidModule(m)
	return m
}

type mojomPicklesProperties struct {
	// list of input files
	Srcs []string
}

type mojomPickles struct {
	android.ModuleBase

	properties mojomPicklesProperties

	generatedSrcs android.Paths
	outDir        android.Path
}

var _ genrule.SourceFileGenerator = (*mojomPickles)(nil)

func (m *mojomPickles) DepsMutator(ctx android.BottomUpMutatorContext) {
	android.ExtractSourcesDeps(ctx, m.properties.Srcs)
}

func (m *mojomPickles) GenerateAndroidBuildActions(ctx android.ModuleContext) {
	m.outDir = android.PathForModuleGen(ctx, "")

	for _, in := range ctx.ExpandSources(m.properties.Srcs, nil) {
		if !strings.HasSuffix(in.Rel(), ".mojom") {
			ctx.PropertyErrorf("srcs", "Source is not a .mojom file: %s", in.Rel())
			continue
		}

		srcRoot := strings.TrimSuffix(in.String(), in.Rel())

		relStem := strings.TrimSuffix(in.Rel(), ".mojom")

		out := android.PathForModuleGen(ctx, relStem+".p")
		m.generatedSrcs = append(m.generatedSrcs, out)

		ctx.ModuleBuild(pctx, android.ModuleBuildParams{
			Rule:   generateMojomPicklesRule,
			Input:  in,
			Output: out,
			Args: map[string]string{
				"package": srcRoot,
				"outDir":  m.outDir.String(),
			},
		})
	}
}

func (m *mojomPickles) GeneratedHeaderDirs() android.Paths {
	return nil
}

func (m *mojomPickles) GeneratedDeps() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomPickles) GeneratedSourceFiles() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomPickles) Srcs() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func mojomPicklesFactory() android.Module {
	m := &mojomPickles{}
	m.AddProperties(&m.properties)
	android.InitAndroidModule(m)
	return m
}

// mojomGenerationProperties are the common properties across the header,
// source and Java source modules.
type mojomGenerationProperties struct {
	// list of input files
	Srcs []string

	// name of the output .srcjar
	Srcjar string

	// name of the templates module
	Templates string

	// Additional flags to pass to the bindings generation script
	Flags string

	// list of pickles modules that will be imported
	Pickles []string

	// list of include paths
	Includes []string

	// list of typemaps modules that will be imported
	Typemaps []string

	// If true, set --use_once_callback flag to the generator.
	// This works only on C++ generation.
	Use_once_callback bool
}

// extractSources adds any necessary dependencies to satisfy filegroup or
// generated sources modules listed in the properties using ":module" syntax,
// if any.
func (p *mojomGenerationProperties) extractSources(ctx android.BottomUpMutatorContext) {
	android.ExtractSourcesDeps(ctx, p.Srcs)
	android.ExtractSourcesDeps(ctx, p.Typemaps)
	android.ExtractSourcesDeps(ctx, p.Pickles)
	android.ExtractSourceDeps(ctx, &p.Templates)
}

// flags generates all needed flags for the build rule.
func (p *mojomGenerationProperties) flags(ctx android.ModuleContext) string {
	flags := []string{}

	for _, typemap := range ctx.ExpandSources(p.Typemaps, nil) {
		flags = append(flags, fmt.Sprintf("--typemap=%s", typemap.String()))
	}
	for _, include := range android.PathsForSource(ctx, p.Includes) {
		flags = append(flags, fmt.Sprintf("-I=%s:%s", include, include))
	}
	for _, pickle := range p.Pickles {
		m := android.SrcIsModule(pickle)
		if m == "" {
			ctx.PropertyErrorf("pickles", "not a module: %q", m)
			continue
		}
		module := ctx.GetDirectDepWithTag(m, android.SourceDepTag).(*mojomPickles)
		flags = append(flags, fmt.Sprintf("--gen_dir=%s", module.outDir.String()))
	}
	if p.Flags != "" {
		flags = append(flags, p.Flags)
	}
	if p.Use_once_callback {
		flags = append(flags, "--use_once_callback")
	}

	return strings.Join(flags, " ")
}

// implicitDeps collects all dependencies of the module.
func (p *mojomGenerationProperties) implicitDeps(ctx android.ModuleContext) android.Paths {
	deps := android.Paths{}
	deps = append(deps, ctx.ExpandSources(p.Pickles, nil)...)
	deps = append(deps, ctx.ExpandSources(p.Typemaps, nil)...)
	deps = append(deps, ctx.ExpandSources([]string{p.Templates}, nil)...)
	return deps
}

// templateDir returns the path where the template .zips are located.
func (p *mojomGenerationProperties) templateDir(ctx android.ModuleContext) string {
	srcFiles := ctx.ExpandSources([]string{p.Templates}, nil)
	if len(srcFiles) == 0 {
		ctx.PropertyErrorf("templates", "module %s does not produce any files", p.Templates)
		return ""
	}
	return path.Dir(srcFiles[0].String())
}

// mojomSrcsRuleDescription has the necessary arguments to perform one
// invocation of generateMojomSrcsRule.
type mojomSrcsRuleDescription struct {
	generatedExtensions []string
	extraFlags          string
}

// generateBuildActions generates all the necessary build actions for the
// current module.
func (p *mojomGenerationProperties) generateBuildActions(
	ctx android.ModuleContext,
	mojomGenerator string,
	descriptions []mojomSrcsRuleDescription,
) android.Paths {
	outDir := android.PathForModuleGen(ctx, "")
	implicitDeps := p.implicitDeps(ctx)
	templateDir := p.templateDir(ctx)
	generatedSrcs := android.Paths{}

	for _, in := range ctx.ExpandSources(p.Srcs, nil) {
		if !strings.HasSuffix(in.Rel(), ".mojom") {
			ctx.PropertyErrorf("srcs", "Source is not a .mojom file: %s", in.Rel())
			continue
		}
		relStem := strings.TrimSuffix(in.Rel(), ".mojom")
		srcRoot := strings.TrimSuffix(in.String(), in.Rel())

		for _, description := range descriptions {
			outs := android.WritablePaths{}
			for _, ext := range description.generatedExtensions {
				out := android.PathForModuleGen(ctx, relStem+ext)
				outs = append(outs, out)
				generatedSrcs = append(generatedSrcs, out)
			}
			ctx.ModuleBuild(pctx, android.ModuleBuildParams{
				Rule:      generateMojomSrcsRule,
				Input:     in,
				Implicits: implicitDeps,
				Outputs:   outs,
				Args: map[string]string{
					"mojomGenerator": mojomGenerator,
					"package":        srcRoot,
					"flags":          fmt.Sprintf("%s %s", p.flags(ctx), description.extraFlags),
					"outDir":         outDir.String(),
					"templateDir":    templateDir,
				},
			})
		}
	}

	return generatedSrcs
}

// mojomHeaders generates all the .h files for a .mojom source.
type mojomHeaders struct {
	android.ModuleBase

	properties mojomGenerationProperties

	exportedHeaderDirs android.Paths
	generatedSrcs      android.Paths
}

var _ genrule.SourceFileGenerator = (*mojomHeaders)(nil)

func (m *mojomHeaders) DepsMutator(ctx android.BottomUpMutatorContext) {
	m.properties.extractSources(ctx)
}

func (m *mojomHeaders) GenerateAndroidBuildActions(ctx android.ModuleContext) {
	m.generatedSrcs = m.properties.generateBuildActions(
		ctx,
		"c++",
		[]mojomSrcsRuleDescription{
			{
				generatedExtensions: []string{".mojom.h"},
				extraFlags:          "",
			},
			{
				generatedExtensions: []string{".mojom-shared.h", ".mojom-shared-internal.h"},
				extraFlags:          "--generate_non_variant_code",
			},
			{
				generatedExtensions: []string{".mojom-shared-message-ids.h"},
				extraFlags:          "--generate_message_ids --generate_non_variant_code",
			},
		},
	)
	m.exportedHeaderDirs = append(m.exportedHeaderDirs, android.PathForModuleGen(ctx, ""))
}

func (m *mojomHeaders) GeneratedHeaderDirs() android.Paths {
	return m.exportedHeaderDirs
}

func (m *mojomHeaders) GeneratedDeps() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomHeaders) GeneratedSourceFiles() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomHeaders) Srcs() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func mojomHeadersFactory() android.Module {
	m := &mojomHeaders{}
	m.AddProperties(&m.properties)
	android.InitAndroidModule(m)
	return m
}

// mojomHeaders generates all the .cc files for a .mojom source.
type mojomSrcs struct {
	android.ModuleBase

	properties mojomGenerationProperties

	generatedSrcs android.Paths
}

var _ genrule.SourceFileGenerator = (*mojomSrcs)(nil)

func (m *mojomSrcs) DepsMutator(ctx android.BottomUpMutatorContext) {
	m.properties.extractSources(ctx)
}

func (m *mojomSrcs) GenerateAndroidBuildActions(ctx android.ModuleContext) {
	m.generatedSrcs = m.properties.generateBuildActions(
		ctx,
		"c++",
		[]mojomSrcsRuleDescription{
			{
				generatedExtensions: []string{".mojom.cc"},
				extraFlags:          "",
			},
			{
				generatedExtensions: []string{".mojom-shared.cc"},
				extraFlags:          "--generate_non_variant_code",
			},
		},
	)
}

func (m *mojomSrcs) GeneratedHeaderDirs() android.Paths {
	return nil
}

func (m *mojomSrcs) GeneratedDeps() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomSrcs) GeneratedSourceFiles() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomSrcs) Srcs() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func mojomSrcsFactory() android.Module {
	m := &mojomSrcs{}
	m.AddProperties(&m.properties)
	android.InitAndroidModule(m)
	return m
}

// mojomHeaders generates the .srcjar file for a set of .mojom source.
type mojomSrcjar struct {
	android.ModuleBase

	properties mojomGenerationProperties

	outDir        android.Path
	generatedSrcs android.Paths
}

var _ genrule.SourceFileGenerator = (*mojomSrcjar)(nil)

func (m *mojomSrcjar) DepsMutator(ctx android.BottomUpMutatorContext) {
	m.properties.extractSources(ctx)
}

func (m *mojomSrcjar) GenerateAndroidBuildActions(ctx android.ModuleContext) {
	srcjars := m.properties.generateBuildActions(
		ctx,
		"java",
		[]mojomSrcsRuleDescription{
			{
				generatedExtensions: []string{".mojom.srcjar"},
				extraFlags:          "",
			},
		},
	)

	out := android.PathForModuleGen(ctx, m.properties.Srcjar)
	ctx.ModuleBuild(pctx, android.ModuleBuildParams{
		Rule:   mergeSrcjarsRule,
		Inputs: srcjars,
		Output: out,
	})
	m.generatedSrcs = append(m.generatedSrcs, out)
}

func (m *mojomSrcjar) GeneratedHeaderDirs() android.Paths {
	return nil
}

func (m *mojomSrcjar) GeneratedDeps() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomSrcjar) GeneratedSourceFiles() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func (m *mojomSrcjar) Srcs() android.Paths {
	return append(android.Paths{}, m.generatedSrcs...)
}

func mojomSrcjarFactory() android.Module {
	m := &mojomSrcjar{}
	m.AddProperties(&m.properties)
	android.InitAndroidModule(m)
	return m
}
